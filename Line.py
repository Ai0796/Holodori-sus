import re
from fractions import Fraction

from sqlalchemy import values
from dataClasses.Metadata import Metadata
from notes.RawNote import RawNote

class Line():
    
    """
    https://gist.github.com/kb10uy/c171c175ba913dc40a73c6ce69da9859
    Example Lines:
    #0023b0:00330x06
    --------------------------------
    First Segment: #0023b0
    002 - Measure 2
    3 - Note class 3 (Hold)
    b - Start position 11 (b in hex) (it goes from 2 - 13 in this game)
    0 - hold note ID 0
    
    Data Segment: 00330x06
    00 - Empty note
    33 - Note type 3, width 3
    0x - Repeat the next number of notes (06)
    06 - Because 0x is before this, add 6 empty notes (00) to the end of the data segment
    --------------------------------
    #0311b:0x03130x04
    --------------------------------
    First Segment: #0311b
    031 - Measure 31
    1 - Note class 1 (Tap)
    b - Start position 11
    
    Data Segment: 0x03130x04
    0x - Repeat the next number of notes (03)
    03 - Because 0x is before this, add 3 empty notes (00) to the end of the data segment
    13 - Note type 1, width 3
    0x - Repeat the next number of notes (04)
    04 - Because 0x is before this, add 4 empty notes (00) to the end of the data segment
    --------------------------------
    #03419:0013
    --------------------------------
    First Segment: #03419
    034 - Measure 34
    1 - Note class 1 (Tap)
    9 - Start position 9
    
    Data Segment: 0013
    00 - Empty note
    13 - Note type 1, width 3
    --------------------------------
    
    The way sus processes measures is based on the length of the data segment
    for example 11 11 11 11 is 4 quarter notes
    11 11 11 11 11 11 11 11 11 would be 8th notes
    0x is used to prevent shorten the data segments
    """
    
    def __init__(self, line, line_number, Score):
        self.line = line.strip()
        self.line_number = line_number
        self.Score = Score
        self.notes = []
        self.type = None

        self.read_line()

    def expandData(self, data):
        expanded_data = ""
        idx = 0
        while idx < len(data):
            if data[idx:idx+2] == '0x':
                # Grab the next two characters and convert base-36 to a decimal integer
                count = int(data[idx+2:idx+4], 36)
                expanded_data += '00' * count
                idx += 4 # Skip past the 4-character "0xYY" block
            else:
                # Standard 2-character note or "00" block
                expanded_data += data[idx:idx+2]
                idx += 2
                
        return expanded_data
    
    def read_line(self):
        
        if match := re.match(r'^#(\w+)\s+(.*)$', self.line):
            self.label, self.data = match.groups()
            self.type = 'metadata'
            self.parseMeta()
            return
            
        elif match := re.match(r'^#(\d{3}[a-z0-9A-Z]{2,3}):(.*)$', self.line):

            self.type = 'note'
            self.label, self.data = match.groups()
            self.parseNote()
            
    def parseMeta(self):
        if not hasattr(self.Score, 'metadata'):
            self.Score.metadata = Metadata()
            
        setattr(self.Score.metadata, self.label.lower(), self.data)
            
        if self.label == 'REQUEST':
            # Handle REQUEST lines if needed
            pass
        
        if self.label == 'WAVEOFFSET':
            # I just have no clue what this does
            # all the meta attributes are underscored but this isn't
            pass
            
    def parseNote(self):
        
        measure = int(self.label[:3])
        note_class = self.label[3]
        start_pos = int(self.label[4], 16)
        long_note_id = None
        
        if note_class == '0' and start_pos == 2:
            ## #mmm02 long segment
            # The measure length after that measure number is specified by the count.
            # Decimal values can be specified. However, a value that is M / 2^n (M, n ∈ N) is preferable.
            return
        
        if len(self.label) > 5:
            ## This will probably not go past 4, but just in case convert from hex
            long_note_id = int(self.label[5:], 16)
            
        data = self.expandData(self.data)
        
        for i in range(0, len(data), 2):
            if data[i: i+2] != '00':
                offset = Fraction(i, len(data))
                width=int(data[i + 1], 36)
                type=int(data[i], 36)

                note = RawNote(measure, note_class, start_pos, long_note_id, width, type, offset, self.line, self.line_number)
                self.notes.append(note)