import dataclasses

@dataclasses.dataclass
class Metadata:
    create_app_verion: str = None
    create_date: str = None
    music_id: str = None
    score_level: str = None
    measure_count: str = None
    full_combo_note_count: str = None
    total_note_count: str = None
    normal_note_count: str = None
    flick_note_count: str = None
    long_start_note_count: str = None
    long_end_note_count: str = None
    long_flick_end_note_count: str = None
    long_relay_note_count: str = None
    long_continue_note_count: str = None
    damage_note_count: str = None
    ghost_note_count: str = None
    waveoffset: str = None
    basebpm: str = None
    
    def __add__(self, other):
        if not isinstance(other, Metadata):
            return NotImplemented
            
        merged_data = {}
        
        for field in dataclasses.fields(self):
            name = field.name
            val_self = getattr(self, name)
            val_other = getattr(other, name)

            merged_data[name] = val_self if val_self is not None else val_other
                
        # Return a brand new Metadata object with the merged data
        return Metadata(**merged_data)
    
    def __radd__(self, other):
        if other == 0:  # This allows sum() to work correctly
            return self
        return self.__add__(other)
    
    def __str__(self):
        return f"Metadata({', '.join(f'{field.name}={getattr(self, field.name)!r}' for field in dataclasses.fields(self))})"