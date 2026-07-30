from Score import Score
from collections import defaultdict

if __name__ == "__main__":
    
    from glob import glob
    
    dataDict = defaultdict(dict)
    
    for fp in glob('beatmaps/Resources/*easy.sus'):
        with open(fp, 'r') as f:
            content = f.readlines()
            
        score = Score(content)
        score.parse()
        
        # print(f"Metadata: {score.metadata}")
        firstNote = min([note.time_offset for note in score.playableNotes if note.time_offset >= 0], default=None)
        lastNote = max([note.time_offset for note in score.playableNotes if note.time_offset >= 0], default=None)
        
        # print(f'Total Length: {lastNote - firstNote} seconds')
        
        musicId = score.metadata.music_id
        length = lastNote - firstNote if firstNote is not None and lastNote is not None else None
        bpm = score.metadata.basebpm
        
        dataDict[musicId]['length'] = length
        dataDict[musicId]['bpm'] = bpm

        # normal_notes = float(score.metadata.normal_note_count)
        # flick_notes = float(score.metadata.flick_note_count) * 1.05
        # long_start_notes = float(score.metadata.long_start_note_count)
        # long_end_notes = float(score.metadata.long_end_note_count)
        # long_flick_end_notes = float(score.metadata.long_flick_end_note_count)
        # long_relay_notes = float(score.metadata.long_relay_note_count) * 0.1
        # long_continue_notes = float(score.metadata.long_continue_note_count) * 0.1
        
        # total_weight = normal_notes + flick_notes + long_start_notes + long_end_notes + long_flick_end_notes + long_relay_notes + long_continue_notes
        
        # real_weight = 0
        
        # for note in score.playableNotes:
        #     real_weight += note.real_weight
        
        # print(fp, f"{score.metadata.score_level}, ", f"{real_weight / 100}")
                    
                    
    dataDict = sorted(dataDict.items(), key=lambda x: x[1]['length'] if x[1]['length'] is not None else float('inf'))
    
    for musicId, data in dataDict:
        print(f"Music ID: {musicId}, Length: {data['length']}, BPM: {data['bpm']}")
                    
    exit()