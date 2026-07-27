from flask import json

from Line import Line
from dataClasses.Metadata import Metadata
from collections import defaultdict
from fractions import Fraction
import math
from notes.PlayableNote import PlayableNote
from slugify import slugify
from rapidfuzz import fuzz, process

class Score():
    
    def __init__(self, content):
        
        self.metadata = Metadata()
        self.lines = []
        self.notes = []
        
        self.skills = []
        self.feverChance = []
        self.fever = []
        
        self.playableNotes = []
        
        self.content = content
        
    def parse(self):
        
        for i, line in enumerate(self.content):
            line = Line(line, i, self)
            self.lines.append(line)
            
            if line.type == 'note':
                self.notes.extend(line.notes)
                
        self.notes.sort(key=lambda note: note.beat)
        
    def addRealTime(self):
        BPM = float(self.metadata.basebpm)
        measureLength = 4
        
        for note in self.playableNotes:
            beat = note.beat
            note.time_offset = (beat * measureLength) / BPM * 60
            
        for skill in self.skills:
            skill.time_offset = (skill.beat * measureLength) / BPM * 60
            
    def addCombo(self):
        self.playableNotes.sort(key=lambda note: note.beat)
        
        for i, note in enumerate(self.playableNotes, 1):
            mult = 1 + (min(i, 1000) // 100) * 0.01
            note.real_weight = note.weight * mult
            
    def weightArraySupport(self, supportLength, supportBoost):
        skills = [note for note in self.skills]
        skills.sort(key=lambda note: note.beat)
        
        returnNotes = []
        skillNum = 0
        
        for note in self.playableNotes:
            
            note.support = 0
            
            if skillNum >= len(skills):
                return
            
            if (note.time_offset >= skills[skillNum].time_offset) and (note.time_offset < skills[skillNum].time_offset + supportLength):
                note.support = supportBoost
                continue
            
            elif note.time_offset >= skills[skillNum].time_offset + supportLength:
                skillNum += 1
                
                
    def defineNotes(self):
        
        combinedNotes = defaultdict(list)
        
        for rawNote in self.notes:
            
            if rawNote.note_description == 'Skill':
                self.skills.append(rawNote)
                
            elif rawNote.note_description == 'Fever Chance':
                self.feverChance.append(rawNote)
                
            elif rawNote.note_description == 'Fever':
                self.fever.append(rawNote)
                
            elif rawNote.note_description == 'Measure Length':
                self.metadata.measureLengths[rawNote.measure] = rawNote.offset
                
            elif rawNote.note_description is None:
                pass
                # print(f"Warning: Note at line {rawNote.line_number} has no description.")
            else:    
                ## when multiple notes overlap, they're combined into a single note with multiple types
                time_position = (rawNote.beat, rawNote.start_pos, rawNote.width)
            
                combinedNotes[time_position].append(rawNote)
            
        combinedNotes = dict(sorted(combinedNotes.items(), key=lambda item: item[0]))
            
        held_notes = {}
        for time_position, notes in combinedNotes.items():
            beat, start_pos, width = time_position
            normal, critical, flick, long_start, long_end, relay, relay_dummy, flick_dummy = [False] * 8
            
            long_note_ids = []
            
            for note in notes:
                if note.note_description == 'Normal':
                    normal = True
                    
                elif note.note_description == 'Gold':
                    critical = True
                    
                elif note.note_description == 'Flick':
                    flick = True
                    
                elif note.note_description == 'Slide Start':
                    long_start = True
                    long_note_ids.append(note.long_note_id)
                    
                ## a slider can end multiple long notes
                elif note.note_description == 'Slide End':
                    long_end = True
                    long_note_ids.append(note.long_note_id)
                    
                elif note.note_description == 'Relay Point':
                    relay = True
                    long_note_ids.append(note.long_note_id)
                    
                elif note.note_description == 'Invisible Relay Point':
                    relay_dummy = True
                    long_note_ids.append(note.long_note_id)
                    
                elif note.note_description == 'Flick Dummy':
                    flick_dummy = True
                    
            if long_start:
                for long_note_id in long_note_ids:
                    held_notes[long_note_id] = (beat, critical)
                    
                    ## Multiple long notes can start from the same position
                    self.playableNotes.append(
                        PlayableNote(
                            measure=int(beat), 
                            start_pos=start_pos,
                            width=width,
                            beat=beat,
                            normal=normal,
                            critical=critical,
                            flick=flick,
                            long_start=long_start,
                            long_mid=False,
                            long_end=long_end,
                            relay=relay,
                            relay_dummy=relay_dummy,
                            flick_dummy=flick_dummy
                        )
                    )
                    
                continue
                
            elif long_end:
                for long_note_id in long_note_ids:
                    start, critical = held_notes[long_note_id]
                    
                    current_long_note = Fraction(math.floor(start * 8) + 1, 8)
                    
                    while current_long_note < beat:
                        self.playableNotes.append(
                            PlayableNote(
                                measure=int(current_long_note), 
                                start_pos=0, ## has to be interpolated, but for now just use 0
                                width=1, ## determined based on relays and such
                                beat=current_long_note,
                                normal=False,
                                critical=critical,
                                flick=False,
                                long_start=False,
                                long_mid=True,
                                long_end=False,
                                relay=False,
                                relay_dummy=False,
                                flick_dummy=False
                            )
                        )
                        
                        current_long_note += Fraction(1, 8)
                        
                    ## Adds a playable note per long note end
                    self.playableNotes.append(
                        PlayableNote(
                            measure=int(beat), 
                            start_pos=start_pos,
                            width=width,
                            beat=beat,
                            normal=normal,
                            critical=critical,
                            flick=flick,
                            long_start=long_start,
                            long_mid=False,
                            long_end=long_end,
                            relay=relay,
                            relay_dummy=relay_dummy,
                            flick_dummy=flick_dummy
                        )
                    )
                    
                continue
                    
            elif relay:
                for long_note_id in long_note_ids:
                    _, critical = held_notes[long_note_id]
                    
                    self.playableNotes.append(
                        PlayableNote(
                            measure=int(beat), 
                            start_pos=start_pos,
                            width=width,
                            beat=beat,
                            normal=normal,
                            critical=critical,
                            flick=flick,
                            long_start=long_start,
                            long_mid=False,
                            long_end=long_end,
                            relay=relay,
                            relay_dummy=relay_dummy,
                            flick_dummy=flick_dummy
                        )
                    )
                    
                continue
                
            elif relay_dummy:
                if not relay:
                    continue
                
            self.playableNotes.append(
                PlayableNote(
                    measure=int(beat), 
                    start_pos=start_pos,
                    width=width,
                    beat=beat,
                    normal=normal,
                    critical=critical,
                    flick=flick,
                    long_start=long_start,
                    long_mid=False,
                    long_end=long_end,
                    relay=relay,
                    relay_dummy=relay_dummy,
                    flick_dummy=flick_dummy
                )
            )
                      

def findSongByName(song):
    with open('masterdata/Music.json', 'r', encoding='utf-8') as f:
        musics = json.load(f)
    
    musicDict = {}

    for music in musics['Music']:
        musicId = music['id']
        musicTitle = None
        
        if 'data' not in music:
            continue
        
        for key, value in music['data'].items():
            if type(value) is str:
                musicTitle = value
                break
        
        musicDict[musicTitle] = (musicId, music)
        
    maxFuzz = -1
        
    for key in musicDict.keys():
        similarity = fuzz.ratio(song.lower(), key.lower())
        if similarity >= maxFuzz:
            maxFuzz = similarity
            bestMatch = key
            
    print(f"Best match for '{song}' is '{bestMatch}' with similarity {maxFuzz}%")
    
    return musicDict[bestMatch][0], musicDict[bestMatch][1]
      
# if __name__ == "__main__":
    
#     from glob import glob
#     import os
#     import pandas
    
#     songList = []
    
#     basicPath = 'charts/sus/*.sus'
#     everythingPath = 'charts/sus/*expert.sus'
    
#     for fp in glob(basicPath):
#         with open(fp, 'r') as f:
#             content = f.readlines()
            
#         score = Score(content)
#         score.parse()
#         score.defineNotes()
#         score.addRealTime()
#         score.addCombo()
        
#         # print(f"Metadata: {score.metadata}")

#         normal_notes = float(score.metadata.normal_note_count)
#         flick_notes = float(score.metadata.flick_note_count) * 1.05
#         long_start_notes = float(score.metadata.long_start_note_count)
#         long_end_notes = float(score.metadata.long_end_note_count)
#         long_flick_end_notes = float(score.metadata.long_flick_end_note_count)
#         long_relay_notes = float(score.metadata.long_relay_note_count) * 0.1
#         long_continue_notes = float(score.metadata.long_continue_note_count) * 0.1
        
#         total_weight = normal_notes + flick_notes + long_start_notes + long_end_notes + long_flick_end_notes + long_relay_notes + long_continue_notes
        
#         real_weight = 0
        
#         for note in score.playableNotes:
#             real_weight += note.real_weight
            
#         fp = os.path.basename(fp).replace('.sus', '').replace('chart_', '')
        
#         # print(os.path.basename(f"{fp}|{total_weight}|{real_weight / 100}"))
#         songList.append([fp, total_weight, real_weight / 100, flick_notes, len(score.playableNotes)])
        
#     # songList = sorted(songList, key=lambda x: x[-1])
    
#     for song in songList:
#         print(f"{song[0]}|{song[1]}|{song[2]}|{song[3]}|{song[4]}")
                    
#     exit()

if __name__ == "__main__":
    import shutil
    
    song = 'Supernova'
    diff = 'expert'
    
    bestMatch, music = findSongByName(song)
    
    print(f"Best match for '{song}' is '{bestMatch}'")
    diffMult = int(music['data']['17'])
    
    beatmapPath = f'beatmaps/Resources/chart_{bestMatch}_{diff}.sus'
    
    shutil.copy(beatmapPath, slugify(f'chart_{song}_{diff}.sus'))
    
    with open(beatmapPath, 'r') as f:
        content = f.readlines()
        
    score = Score(content)
    score.parse()
    score.defineNotes()
    score.addRealTime()
    score.addCombo()
    score.playableNotes.sort(key=lambda note: note.beat)
    
    # for i, note in enumerate(score.playableNotes):
    #     print(i, note)

    print(len(score.lines))
    print(len(score.playableNotes))
    print(score.metadata)
    
    weightList = [
        ['time_offset', 'beat', 'weight', 'real_weight']
    ]
    
    bp = 198152
    bonus = 0.497
    difficulty = 26
    
    with open('rawNotes.csv', 'w') as f:
        for note in score.notes:
            f.write(f"{note.line_number}, {note.line}, {note.note_class}, {note.note_type}, {note.measure}, {note.start_pos}, {note.width}, {float(note.beat)}, {note.note_description}\n")
    
    totalWeight = 0
    baseWeight = 0
    
    for note in score.playableNotes:
        totalWeight += note.real_weight
        baseWeight += note.weight
        # weightList.append(
        #     [str(note.time_offset), str(float(note.beat)), str(note.weight), str(note.real_weight)]
        # )
        
    normal_notes = []
    flick_notes = []
    long_start_notes = []
    long_end_notes = []
    long_flick_end_notes = []
    long_relay_notes = []
    long_continue_notes = []
        
    for note in score.playableNotes:
        
        if note.long_start:
            long_start_notes.append(note)
            
        elif note.long_end:
            if note.flick:
                long_flick_end_notes.append(note)
            else:
                long_end_notes.append(note)
                
        elif note.long_mid:
            long_continue_notes.append(note)
                
        elif note.relay:
            long_relay_notes.append(note)
            
        elif note.flick:
            flick_notes.append(note)
            
        else:
            normal_notes.append(note)
        
        weightList.append(
            [str(note.time_offset), str(float(note.beat)), str(note.weight), str(note.real_weight), str(note.real_weight / totalWeight)]
        )
        
    print(f'Normal Note Count: {len(normal_notes)}')
    print(f'Flick Note Count: {len(flick_notes)}')
    print(f'Long Start Note Count: {len(long_start_notes)}')
    print(f'Long End Note Count: {len(long_end_notes)}')
    print(f'Long Flick End Note Count: {len(long_flick_end_notes)}')
    print(f'Long Relay Note Count: {len(long_relay_notes)}')
    print(f'Long Continue Note Count: {len(long_continue_notes)}')
    print(f'Total Notes: {len(score.playableNotes)}')
    
    print(f'Total Weight: {totalWeight / 100:.2f}')
    print(f'Base Weight: {baseWeight / 100:.2f}')
    
    singleNote = 100 / baseWeight
    difficultyMult = 1 + (difficulty - 5) * (diffMult / 1000)
    
    
    print(f'Single Note Base Weight: {singleNote}')
    print(f'Difficulty Multiplier: {difficultyMult:.3f}')
    print(f'BP Multiplier: {bp:.2f}')
    singleNote = singleNote * difficultyMult * bp * 2.3
    
    diff = 637 / singleNote
    print(f'Difficulty: {diff}')
    
    print(f'Single Note Weight: {singleNote:.2f}')