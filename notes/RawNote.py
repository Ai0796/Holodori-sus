class RawNote:
    def __init__(self, measure, note_class, start_pos, long_note_id, width, note_type, offset, line, line_number):
        
        note_class, note_type = int(note_class), int(note_type)
        
        self.measure = measure
        self.note_class = note_class
        self.start_pos = start_pos
        self.long_note_id = long_note_id
        self.width = width
        self.note_type = note_type
        self.offset = offset
        self.line = line
        self.line_number = line_number
        self.beat = measure + offset
        
        self.note_description = None
        
        if measure == 0 and note_class == 0 and start_pos == 2:
            self.note_description = 'Measure Length'
            return
        
        if note_class == 0:
            if start_pos == 11:
                self.note_description = 'Skill'
                
            ## Both fever chance and fever have two notes, for start and end
            if start_pos == 12:
                self.note_description = 'Fever Chance'
                
            if start_pos == 13:
                self.note_description = 'Fever'
                
        if note_class == 1:
            if note_type == 1:
                self.note_description = 'Normal'
                
            if note_type == 2:
                self.note_description = 'Gold'
                
            if note_type == 3:
                self.note_description = 'Relay Dummy'
                
        if note_class == 3:
            if note_type == 1:
                self.note_description = 'Slide Start'
            
            if note_type == 2:
                self.note_description = 'Slide End'
                
            ## Relay points are used for slide layout, but don't affect score
            if note_type == 3:
                self.note_description = 'Relay Point'
                
            if note_type == 4:
                self.note_description = 'Bezier Control Point' ## Probably won't be used
                
            if note_type == 5:
                self.note_description = 'Invisible Relay Point'
                
        if note_class == 5:
            if note_type == 1:
                self.note_description = 'Flick'
                
            ## for some reason these match up with slide notes and are dummies
            ## I think it might be what it uses to tell the game to draw curves for slides
            if note_type == 2:
                self.note_description = 'Flick Down'
                
            if note_type == 6:
                self.note_description = 'Flick Dummy'
                
        # if self.note_description is None:
        #     print(note_class, note_type)
                
    def __str__(self):
        return f"Measure: {self.measure}, Offset: {self.offset}, Class: {self.note_class}, Start Pos: {self.start_pos}, Long Note ID: {self.long_note_id}, Width: {self.width}, Type: {self.note_type}, Line Number: {self.line_number}, Description: {getattr(self, 'note_description', 'N/A')}"