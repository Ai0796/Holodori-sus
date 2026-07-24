class PlayableNote():
    def __init__(self, measure, start_pos, width, beat,
                 normal, critical, flick, long_start, long_end, long_mid, relay, relay_dummy, flick_dummy):
        self.measure = measure
        self.start_pos = start_pos
        self.width = width
        self.beat = beat
        
        self.normal = normal
        self.critical = critical
        self.flick = flick
        self.long_start = long_start
        self.long_end = long_end
        self.long_mid = long_mid
        self.relay = relay
        self.relay_dummy = relay_dummy
        self.flick_dummy = flick_dummy
        
        self.weight = -1
        self.time_offset = -1
        self.real_weight = -1
        
        self.processNote()
        
    def processNote(self):
        
        self.weight = 10
        
        if self.long_mid or self.relay:
            self.weight = 1
            
        if self.critical and self.flick:
            self.weight *= 3
            
        elif self.critical:
            self.weight *= 2
        self.real_weight = self.weight
        
    def to_str(self):
        properties = [
            'time_offset',
            'weight',
            'beat',
            'measure',
            'start_pos',
            'width',
            'normal',
            'critical',
            'flick',
            'long_start',
            'long_end',
            'long_mid',
            'relay',
            'relay_dummy',
            'flick_dummy'
        ]
        
        returnStr = 'PlayableNote('
        
        for i, prop in enumerate(properties):
            value = getattr(self, prop)
            if value is False:
                continue
            returnStr += f"{prop}={value}"
            returnStr += ", "
            
        returnStr = returnStr.rstrip(", ")
        returnStr += ")"
        return returnStr
            
    def __repr__(self):
        return self.to_str()
    
    def __str__(self):
        return self.to_str()