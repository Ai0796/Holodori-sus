import shutil
from slugify import slugify
from scripts.findSongByName import findSongByName

from Score import Score

def main(song, diff):
    
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

if __name__ == "__main__":
    
    song = 'm0321'
    diff = 'normal'

    main(song, diff)