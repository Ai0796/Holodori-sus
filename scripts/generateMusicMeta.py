from Score import Score
from glob import glob
import os
import json
import re
import traceback
from tqdm import tqdm

masterPath = 'master_data/json/'
DIFFICULTIES = ['Easy', 'Normal', 'Hard', 'Expert']

class MasterData():
    
    def __init__(self):
        for fp in glob(masterPath + '*.json'):
            setattr(self, os.path.splitext(os.path.basename(fp))[0], json.load(open(fp, 'r', encoding='utf-8')))
            
class Lang():
    
    def __init__(self, language='Eng'):
        self.language = language
        self.langPath = f'master_data/json/Lang*{language}.json'
        
        for fp in glob(self.langPath):
            
            assetName = re.match(r'Lang(.+)_\w+\.json', os.path.basename(fp)).group(1)
            
            addDict = {}
            
            with open(fp, 'r', encoding='utf-8') as f:
                for value in json.load(f):
                    
                    if 'id' in value:
                    
                        addDict[value['id']] = value.get('text', None)

            setattr(self, assetName, addDict)

masterData = MasterData()
langData = Lang(language='Eng')

## Example m0129
def getMusicData(assetId):
    for music in masterData.Music:
        if music['id'] == assetId:
            return music
        
def getMusicDifficulty(assetId, difficulty):
    diffKey = f'MUSIC_DIFFICULTY_TYPE_{difficulty}'.upper()
    for music in masterData.MusicDifficulty:
        if music['musicId'] == assetId and music['difficultyType'] == diffKey:
            return music

if __name__ == "__main__":
    
    songList = []
    failedList = []
    
    basicPath = 'beatmaps/Resources/*.sus'
    
    for fp in tqdm(glob(basicPath), desc="Processing charts"):
        try:
            with open(fp, 'r') as f:
                content = f.readlines()
                
            basename = os.path.basename(fp)
            asset, diff = re.match(r'chart_(m\d{4})_(\w+)\.sus', basename).groups()
            
            music = getMusicData(asset)
            musicDiff = getMusicDifficulty(asset, diff)
                
            score = Score(content)
            score.parse()

            normal_notes = float(score.metadata.normal_note_count) * 1000
            flick_notes = float(score.metadata.flick_note_count) * 1050
            long_start_notes = float(score.metadata.long_start_note_count) * 1000
            long_end_notes = float(score.metadata.long_end_note_count) * 1000
            long_flick_end_notes = float(score.metadata.long_flick_end_note_count) * 1000
            long_relay_notes = float(score.metadata.long_relay_note_count) * 100
            long_continue_notes = float(score.metadata.long_continue_note_count) * 100
            
            total_weight = normal_notes + flick_notes + long_start_notes + long_end_notes + long_flick_end_notes + long_relay_notes + long_continue_notes
            
            base_weight_calc = 0
            real_weight = 0
            
            for note in score.playableNotes:
                base_weight_calc += note.weight
                real_weight += note.real_weight
                
            fp = os.path.basename(fp).replace('.sus', '').replace('chart_', '')
            
            chart = {}
            
            chart['musicId'] = music['id']
            chart['titleLangId'] = music['titleLangId']
            chart['title'] = langData.Music.get(music['titleLangId'], music['titleLangId'])
            chart['liveScoreCoefficientPermil'] = music['liveScoreCoefficientPermil']
            chart['playingSeconds'] = music['playingSeconds']
            chart['beatmapSeconds'] = float(max(score.playableNotes, key=lambda note: note.time_offset).time_offset)
            chart['chorusStartMillisecond'] = music['chorusStartMillisecond']
            chart['chorusEndMillisecond'] = music['chorusEndMillisecond']
            chart['difficulty'] = diff
            chart['difficultyLevel'] = musicDiff['difficultyLevel']
            chart['measure_count'] = int(score.metadata.measure_count)
            chart['basebpm'] = float(score.metadata.basebpm)
            chart['full_combo_note_count'] = int(score.metadata.full_combo_note_count)
            chart['normalNoteCount'] = int(score.metadata.normal_note_count)
            chart['flickNoteCount'] = int(score.metadata.flick_note_count)
            chart['longStartNoteCount'] = int(score.metadata.long_start_note_count)
            chart['longEndNoteCount'] = int(score.metadata.long_end_note_count)
            chart['longFlickEndNoteCount'] = int(score.metadata.long_flick_end_note_count)
            chart['longRelayNoteCount'] = int(score.metadata.long_relay_note_count)
            chart['longContinueNoteCount'] = int(score.metadata.long_continue_note_count)
            chart['base_weight'] = int(total_weight)
            chart['combo_weight'] = int(real_weight)
            
            fever_chance = sorted([note.time_offset for note in score.feverChance])
            fever_chance_start = fever_chance[0] if fever_chance else None
            fever_chance_end = fever_chance[1] if fever_chance else None
            
            fever = sorted([note.time_offset for note in score.fever])
            fever_start = fever[0] if fever else None
            fever_end = fever[1] if len(fever) > 1 else 0
            
            chart['feverChanceStart'] = float(fever_chance_start)
            chart['feverChanceEnd'] = float(fever_chance_end)
            
            chart['feverStart'] = float(fever_start)
            chart['feverEnd'] = float(fever_end)
            
            chart['supportSkills'] = []
            chart['notes'] = []
            
            if base_weight_calc != total_weight:
                print(f"Warning: Base weight calculation mismatch for {fp}. Calculated: {base_weight_calc}, Total: {total_weight}")
                failedList.append([fp, base_weight_calc, total_weight])
                continue
            
            for skill in score.skills:
                chart['supportSkills'].append(float(skill.time_offset))
            
            for note in score.playableNotes:
                chart['notes'].append(
                    [float(note.time_offset), int(note.real_weight)]
                )
                
            songList.append(chart)
            
        except:
            print(f"Error processing file: {fp}")
            traceback.print_exc()
            break
            continue
    # songList = sorted(songList, key=lambda x: x[-1])
    
    print(f'Processed {len(songList)} charts.')
    print(f'Failed to process {len(failedList)} charts.')
    print(f'Total charts: {len(list(glob(basicPath)))}')
    
    with open('failed_charts.txt', 'w') as f:
        for item in failedList:
            f.write(f"{item[0]} - Calculated: {item[1]}, Total: {item[2]}\n")
    
    with open('music_meta.json', 'w') as f:
        json.dump(songList, f, indent=4)