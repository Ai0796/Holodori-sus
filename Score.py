from Line import Line
from dataClasses.Metadata import Metadata
from collections import defaultdict
from fractions import Fraction
import math
from notes.PlayableNote import PlayableNote

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
                    
                elif note.note_description == 'Relay Point' or note.note_description == 'Invisible Relay Point':
                    relay = True
                    long_note_ids.append(note.long_note_id)
                    
                elif note.note_description == 'Flick Dummy':
                    flick_dummy = True
                    
            if long_start:
                for long_note_id in long_note_ids:
                    held_notes[long_note_id] = (beat, critical)
                
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
                    
            elif relay:
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
                      
                      
          
                    

if __name__ == "__main__":
    with open('charts/sus/chart_snow halation_expert.sus', 'r') as f:
        content = f.readlines()
        
    score = Score(content)
    score.parse()
    score.defineNotes()
    score.addRealTime()
    score.playableNotes.sort(key=lambda note: note.beat)
    
    for i, note in enumerate(score.playableNotes):
        print(i, note)

    print(len(score.lines))
    print(len(score.playableNotes))
    print(score.metadata)
    
    weightList = [
        ['time_offset', 'beat', 'weight']
    ]
    
    for note in score.playableNotes:
        weightList.append(
            [str(note.time_offset), str(float(note.beat)), str(note.weight)]
        )
        
    with open('output.csv', 'w') as f:
        for row in weightList:
            f.write(','.join(row) + '\n')