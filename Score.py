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
        
        self.parseRealTime()
        self.filterNotes()
        self.defineNotes()
        self.addTimePlayableNotes()
        self.addCombo()
        
    def parseRealTime(self):
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
            currentTime += (beatOffset) / currentBPM * 60
            
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
    
    # Because time_offsets are calculated before playable notes, we need to add them in again
    def addTimePlayableNotes(self):
        
        notes = self.playableNotes + self.bpmChanges
        notes = sorted(notes, key=lambda note: note.beat)
        
        currentBPM = self.base_bpm
        
        lastBeat = 0
        currentTime = 0
        
        for note in notes:
            
            beatDiff = note.beat - lastBeat
            currentTime += beatDiff / currentBPM * 60
            
            if hasattr(note, 'note_description') and note.note_description == 'BPM Change':
                bpm_num = note.width
                currentBPM = Fraction(self.BPMs[bpm_num])
            
            lastBeat = note.beat
            
            note.time_offset = currentTime
            
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
                            measure=note.measure, 
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
                            measure=note.measure, 
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
                                measure=note.measure, ## This may be inaccurate, but as measure is not used other than debugging, it is not a priority
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
                            measure=note.measure, 
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
                        measure=note.measure, 
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