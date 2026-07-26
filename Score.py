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
            
    def addCombo(self):
        self.playableNotes.sort(key=lambda note: note.beat)
        
        for i, note in enumerate(self.playableNotes, 1):
            mult = 1 + ((i) // 100) * 0.01
            note.real_weight = note.weight * mult
                
                
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
        
        musicDict[musicTitle] = musicId
        
    maxFuzz = -1
        
    for key in musicDict.keys():
        similarity = fuzz.ratio(song.lower(), key.lower())
        if similarity >= maxFuzz:
            maxFuzz = similarity
            bestMatch = key
            
    print(f"Best match for '{song}' is '{bestMatch}' with similarity {maxFuzz}%")
    
    return musicDict[bestMatch]
      
# if __name__ == "__main__":
    
#     from glob import glob
    
#     for fp in glob('charts/sus/*.sus'):
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
        
#         print(fp, f"{score.metadata.score_level}, ", f"{real_weight / 100}")
                    
                    
#     exit()

if __name__ == "__main__":
    import shutil
    
    song = 'BIBBIDIBA'
    diff = 'expert'
    
    bestMatch = findSongByName(song)
    
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
    
    bp = 511253
    
    yInt = 0.5413
    m = 0.004
    difficulty = 26
    
    estimatedWeight = m * difficulty + yInt 
    estimatedWeight = estimatedWeight * (bp)
    
    print(estimatedWeight)
    
    with open('rawNotes.csv', 'w') as f:
        for note in score.notes:
            f.write(f"{note.line_number}, {note.line}, {note.note_class}, {note.note_type}, {note.measure}, {note.start_pos}, {note.width}, {float(note.beat)}, {note.note_description}\n")
    
    totalWeight = 0
    
    for note in score.playableNotes:
        totalWeight += note.real_weight
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
            [str(note.time_offset), str(float(note.beat)), str(note.weight), str(note.real_weight), str(note.real_weight / totalWeight * estimatedWeight)]
        )
        
    print(f'Normal Note Count: {len(normal_notes)}')
    print(f'Flick Note Count: {len(flick_notes)}')
    print(f'Long Start Note Count: {len(long_start_notes)}')
    print(f'Long End Note Count: {len(long_end_notes)}')
    print(f'Long Flick End Note Count: {len(long_flick_end_notes)}')
    print(f'Long Relay Note Count: {len(long_relay_notes)}')
    print(f'Long Continue Note Count: {len(long_continue_notes)}')
    print(f'Total Notes: {len(score.playableNotes)}')
        
    with open('output.csv', 'w') as f:
        for row in weightList:
            f.write(','.join(row) + '\n')