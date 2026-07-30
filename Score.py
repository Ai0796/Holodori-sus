from flask import json

from Line import Line
from dataClasses.Metadata import Metadata
from collections import defaultdict
from fractions import Fraction
import math
from notes.PlayableNote import PlayableNote
from slugify import slugify
from rapidfuzz import fuzz, process

from lib.master_data import MasterData
from lib.language import Lang

masterdata = MasterData()
lang = Lang()

class Score():
    
    def __init__(self, content):
        
        self.metadata = Metadata()
        self.lines = []
        self.notes = []
        
        self.skills = []
        self.feverChance = []
        self.fever = []
        self.measureLengths = []
        self.BPMs = {}
        self.bpmChanges = []
        
        self.playableNotes = []
        self.combinedNotes = defaultdict(list)
        
        self.content = content
        self.base_bpm = None
        self.eight_note_duration = None
        
    def parse(self):
        
        for i, line in enumerate(self.content):
            line = Line(line, i, self)
            self.lines.append(line)
            
            if line.type == 'note':
                self.notes.extend(line.notes)
        
        self.base_bpm = Fraction(self.metadata.basebpm)
        
        self.addRealTime()
        self.filterNotes()
        
    def addRealTime(self):
        measureLength = 4
        currentBPM = self.base_bpm
        
        allNotes = self.notes
        allNotes.sort(key=lambda note: note.measure + note.offset)
        
        lastMeasure = 0
        lastOffset = 0
        lastBeat = 0
        currentTime = 0
        
        for note in allNotes:
            
            measureDiff = note.measure - lastMeasure
            beatOffset = (note.offset - lastOffset + measureDiff) * measureLength
            currentTime += (beatOffset * measureLength) / currentBPM * 60
            
            if note.note_description and note.note_description == 'BPM Change':
                bpm_num = note.width
                currentBPM = Fraction(self.BPMs[bpm_num])
            
            if note.note_description and note.note_description == 'Measure Length':
                measureLength = Fraction(note.note_type)
            
            note.time_offset = currentTime
            note.beat = lastBeat + beatOffset
            
            lastBeat = note.beat
            lastMeasure = note.measure
            lastOffset = note.offset
            
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
                
    def filterNotes(self):
        for rawNote in self.notes:
            
            if rawNote.note_description is None:
                continue
                    
            if rawNote.note_description == 'Skill':
                self.skills.append(rawNote)
                
            elif rawNote.note_description == 'Fever Chance':
                self.feverChance.append(rawNote)
                
            elif rawNote.note_description == 'Fever':
                self.fever.append(rawNote)
                
            elif rawNote.note_description == 'Measure Length':
                self.measureLengths.append(rawNote)
                
            elif rawNote.note_description == 'BPM Change':
                self.bpmChanges.append(rawNote)
                
            elif 'ghost' in rawNote.note_description.lower():
                pass
                # print(f"Warning: Note at line {rawNote.line_number} has no description.")
            
            else:    
                ## when multiple notes overlap, they're combined into a single note with multiple types
                time_position = (rawNote.beat, rawNote.start_pos, rawNote.width)
            
                self.combinedNotes[time_position].append(rawNote)
                
    def defineNotes(self):

        combinedNotes = dict(sorted(self.combinedNotes.items(), key=lambda item: [float(item[0][0]), item[0][1], item[0][2]]))
            
        held_notes = {}
        for time_position, notes in combinedNotes.items():
            beat, start_pos, width = time_position
            normal, critical, flick, long_start, long_end, relay, relay_dummy, flick_dummy = [False] * 8
            
            long_note_ids = []
            long_ends = []
            
            for note in notes:
                
                time_offset = note.time_offset
                
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
                    long_ends.append(note.long_note_id)
                    long_end = True
                    
                elif note.note_description == 'Relay Point':
                    relay = True
                    long_note_ids.append(note.long_note_id)
                    
                elif note.note_description == 'Invisible Relay Point':
                    relay_dummy = True
                    # long_note_ids.append(note.long_note_id)
                    
                elif note.note_description == 'Measure Length':
                    currentMeasureLength = note.note_type
                    
            if long_start:
                for long_note_id in long_note_ids:
                    held_notes[long_note_id] = (beat, critical, time_offset)
                    
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
                            relay=relay
                        )
                    )

            
            if relay:
                for long_note_id in long_note_ids:
                    
                    _, critical, start_time_offset = held_notes[long_note_id]
                    
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
                            relay=relay
                        )
                    )

                
            if long_end:
                # print(f"Long end note at beat {beat} {float(beat)} with long_note_ids: {long_note_ids}")
                for long_note_id in long_ends:
                    start, critical, start_time_offset = held_notes[long_note_id]
                    
                    current_long_note =  Fraction(math.floor(start * 2) + 1, 2)
                    
                    i = 0
                    
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
                                relay=False
                            )
                        )
                        
                        current_long_note += Fraction(1, 2)
                        i += 1

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
                            relay=False
                        )
                    )

                
            ## relay_dummy is used to indicate a hold relay that isn't a note, it only changes the position of a hold
            if relay_dummy:
                if not relay:
                    continue
                
            if not long_start and not long_end and not relay:
                
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
                        relay=relay
                    )
                )
                      

def findSongByName(song):
    
    musicDict = {}
    
    maxFuzz = -1

    for musicId, name in lang.Music.items():

        if 'title' not in musicId:
            continue

        similarity = fuzz.ratio(song.lower(), name.lower())
        if similarity >= maxFuzz:
            maxFuzz = similarity
            bestMatch = musicId
            
    for music in masterdata.Music:
        
        similarity = fuzz.ratio(song.lower(), music['id'].lower())
        if similarity >= maxFuzz:
            maxFuzz = similarity
            bestMatch = music
            
        elif music['titleLangId'] == bestMatch:
            bestMatch = music
            
    print(f"Best match for '{song}' is '{bestMatch["id"]}' with similarity {maxFuzz}%")
    
    return bestMatch['id'], bestMatch

if __name__ == "__main__":
    import shutil
    
    song = 'm0321'
    diff = 'normal'
    
    bestMatch, music = findSongByName(song)
    
    print(f"Best match for '{song}' is '{bestMatch}'")
    diffMult = music['liveScoreCoefficientPermil']
    try:
        diffMult = int(diffMult)
    except:
        diffMult = 0
    
    beatmapPath = f'beatmaps/Resources/chart_{bestMatch}_{diff}.sus'
    
    shutil.copy(beatmapPath, slugify(f'chart_{song}_{diff}.sus'))
    
    with open(beatmapPath, 'r') as f:
        content = f.readlines()
        
    score = Score(content)
    score.parse()
    score.defineNotes()
    score.playableNotes.sort(key=lambda note: note.beat)
    
    # for i, note in enumerate(score.playableNotes):
    #     print(i, note)

    print(len(score.lines))
    print(len(score.playableNotes))
    print(score.metadata)
    print(score.BPMs, score.bpmChanges)
    
    weightList = [
        ['time_offset', 'beat', 'weight', 'real_weight']
    ]
    
    bp = 198152
    bonus = 0.497
    difficulty = 26
    
    with open('rawNotes.csv', 'w') as f:
        f.write('line_number, line, note_class, note_type, measure, beat, start_pos, width, beat_float, note_description\n')
        for note in score.notes:
            f.write(f"{note.line_number}, {note.line}, {note.note_class}, {note.note_type}, {note.measure}, {float(note.beat)}, {note.start_pos}, {note.width}, {float(note.beat)}, {note.note_description}\n")
    
    with open('playableNotes.csv', 'w') as f:
        f.write('measure, start_pos, width, beat_float, normal, critical, flick, long_start, long_mid, long_end, relay, weight, real_weight\n')
        for note in score.playableNotes:
            f.write(f"{note.measure}, {note.start_pos}, {note.width}, {float(note.beat)}, {note.normal}, {note.critical}, {note.flick}, {note.long_start}, {note.long_mid}, {note.long_end}, {note.relay}, {note.weight}, {note.real_weight}\n")
        
    
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
            
        elif note.relay:
            long_relay_notes.append(note)
            
        elif note.long_end:
            if note.flick:
                long_flick_end_notes.append(note)
            else:
                long_end_notes.append(note)
                
        elif note.long_mid:
            long_continue_notes.append(note)
            
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
    
    print(f'Total Weight: {totalWeight / 1000:.2f}')
    print(f'Base Weight: {baseWeight / 1000:.2f}')
    
    singleNote = 100 / baseWeight
    difficultyMult = 1 + (difficulty - 5) * (diffMult / 1000)
    
    
    print(f'Single Note Base Weight: {singleNote}')
    print(f'Difficulty Multiplier: {difficultyMult:.3f}')
    print(f'BP Multiplier: {bp:.2f}')
    singleNote = singleNote * difficultyMult * bp * 2.3
    
    diff = 637 / singleNote
    print(f'Difficulty: {diff}')
    
    print(f'Single Note Weight: {singleNote:.2f}')