from Score import Score, findSongByName
from glob import glob
import os
import json
import re

masterPath = 'master_data/json/'
DIFFICULTIES = ['Easy', 'Normal', 'Hard', 'Expert']

class MasterData():
    
    def __init__(self):
        for fp in glob(masterPath + '*.json'):
            setattr(self, os.path.splitext(os.path.basename(fp))[0], json.load(open(fp, 'r', encoding='utf-8')))
            
class Lang():
    
    def __init__(self, language='Eng'):
        self.language = language
        self.langPath = f'master_data/lang/Lang*{language}.json'
        
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
    
    basicPath = 'beatmaps/Resources/*.sus'
    
    for fp in glob(basicPath):
        try:
            with open(fp, 'r') as f:
                content = f.readlines()
                
            basename = os.path.basename(fp)
            asset, diff = re.match(r'chart_(m\d{4})_(\w+)\.sus', basename).groups()
            
            music = getMusicData(asset)
            musicDiff = getMusicDifficulty(asset, diff)
                
            score = Score(content)
            score.parse()
            score.defineNotes()
            score.addRealTime()
            score.addCombo()

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
            chart['difficulty'] = diff
            chart['difficultyLevel'] = musicDiff['difficultyLevel']
            chart['normalNoteCount'] = int(score.metadata.normal_note_count)
            chart['flickNoteCount'] = int(score.metadata.flick_note_count)
            chart['longStartNoteCount'] = int(score.metadata.long_start_note_count)
            chart['longEndNoteCount'] = int(score.metadata.long_end_note_count)
            chart['longFlickEndNoteCount'] = int(score.metadata.long_flick_end_note_count)
            chart['longRelayNoteCount'] = int(score.metadata.long_relay_note_count)
            chart['longContinueNoteCount'] = int(score.metadata.long_continue_note_count)
            chart['base_weight'] = int(total_weight)
            chart['combo_weight'] = int(real_weight)
            
            chart['supportSkills'] = []
            chart['notes'] = []
            
            if base_weight_calc != total_weight:
                print(f"Warning: Base weight calculation mismatch for {fp}. Calculated: {base_weight_calc}, Total: {total_weight}")
                continue
            
            for skill in score.skills:
                chart['supportSkills'].append(skill.time_offset)
            
            for note in score.playableNotes:
                chart['notes'].append(
                    [note.time_offset, int(note.real_weight)]
                )
                
            songList.append(chart)
            
        except:
            print(f"Error processing file: {fp}")
            continue
    # songList = sorted(songList, key=lambda x: x[-1])
    
    print(f'Processed {len(songList)} charts.')
    print(f'Total charts: {len(list(glob(basicPath)))}')
    
    with open('music_meta.json', 'w') as f:
        json.dump(songList, f, indent=4)