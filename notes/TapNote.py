from RawNote import RawNote

class TapNote(RawNote):
    def __init__(self, measure, note_class, start_pos, line_number, width, type):
        super().__init__(measure, note_class, start_pos, line_number, width, type)