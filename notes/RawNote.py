class RawNote:
    def __init__(self, measure, note_class, start_pos, long_note_id, width, note_type, offset, line, line_number):
        
        note_class, note_type = float(note_class), float(note_type)
        
        self.measure = measure
        self.note_class = note_class
        self.start_pos = start_pos
        self.long_note_id = long_note_id
        self.width = width
        self.note_type = note_type
        self.offset = offset
        self.line = line
        self.line_number = line_number
        # self.beat = measure + offset
        
        self.note_description = None
        self.time_offset = None
        
        """
        EventTypeTap = "1";
        EventTypeDirectional = "5";
        EventTypeLong = "3";
        EventTypeGhost = "6";
        
        TapValueDefault = 1;
        TapValueCritical = 2;
        TapValueLongRelayDeActive = 3;
        TapValueDamage = 8;
        TapValueGhostRelay = 9;
        DirectionalValueFlickOrLongFlickEnd = 1;
        DirectionalValueLongEaseIn = 2;
        DirectionalValueLongEaseOut = 6;
        DirectionalValueGhostEaseIn = 4;
        DirectionalValueGhostEaseOut = 7;
        LongValueStart = 1;
        LongValueEndOrFlickEnd = 2;
        LongValueRelayActive = 3;
        LongValueBezierPoint = 4;
        LongValueRelayDeActive = 5;
        GhostValueStart = 1;
        GhostValueEnd = 2;
        GhostValueRelay = 3;
        GhostValueLineTypeEaseIn = 4;
        GhostValueLineTypeEaseOut = 7;
        """
        
        if note_class == 0:
            
            if start_pos == 2:
                self.note_description = 'Measure Length'
            
            elif start_pos == 8:
                self.note_description = 'BPM Change'
                
            elif start_pos == 10:
                self.note_description = None
            
            elif start_pos == 11:
                self.note_description = 'Skill'
                
            ## Both fever chance and fever have two notes, for start and end
            elif start_pos == 12:
                self.note_description = 'Fever Chance'
                
            elif start_pos == 13:
                self.note_description = 'Fever'
                
            else:
                print(f"Unknown note class 0 with start_pos {start_pos} at measure {measure} and offset {offset}")
                
        elif note_class == 1:
            if note_type == 1:
                self.note_description = 'Normal'
                
            elif note_type == 2:
                self.note_description = 'Gold'
                
            elif note_type == 3:
                self.note_description = 'Relay Dummy'
                
            elif note_type == 8:
                self.note_description = 'Damage'
                
            elif note_type == 9:
                self.note_description = 'Ghost Relay'
                
        elif note_class == 3:
            if note_type == 1:
                self.note_description = 'Slide Start'
            
            elif note_type == 2:
                self.note_description = 'Slide End'
                
            ## Relay points are used for slide layout, but don't affect score
            elif note_type == 3:
                self.note_description = 'Relay Point'
                
            elif note_type == 4:
                self.note_description = 'Bezier Control Point' ## Probably won't be used
                
            elif note_type == 5:
                self.note_description = 'Invisible Relay Point'
                
        elif note_class == 5:
            if note_type == 1:
                self.note_description = 'Flick'
                
            ## for some reason these match up with slide notes and are dummies
            ## I think it might be what it uses to tell the game to draw curves for slides
            elif note_type == 2:
                self.note_description = 'Directional Ease Out'
                
            elif note_type == 4:
                self.note_description = 'Ghost Flick Ease In'
                
            elif note_type == 6:
                self.note_description = 'Directional Ease In'
                
            elif note_type == 7:
                self.note_description = 'Ghost Flick Ease Out'
                
        elif note_class == 6:
            if note_type == 1:
                self.note_description = 'Ghost Start'
                
            elif note_type == 2:
                self.note_description = 'Ghost End'
                
            elif note_type == 3:
                self.note_description = 'Ghost Relay'
                
            elif note_type == 4:
                self.note_description = 'Ghost Ease In'
                
            if note_type == 7:
                self.note_description = 'Ghost Ease Out'
                
        else:
            print(f"Unknown note class {note_class} with start_pos {start_pos} at measure {measure} and offset {offset}")
                
    def __str__(self):
        return f"Measure: {self.measure}, Offset: {self.offset}, Class: {self.note_class}, Start Pos: {self.start_pos}, Long Note ID: {self.long_note_id}, Width: {self.width}, Type: {self.note_type}, Line Number: {self.line_number}, Description: {getattr(self, 'note_description', 'N/A')}"