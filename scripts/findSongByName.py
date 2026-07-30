from lib.master_data import MasterData
from lib.language import Lang
from rapidfuzz import fuzz, process

masterdata = MasterData()
lang = Lang()

def findSongByName(song):
    
    musicDict = {}
    
    maxFuzz = -1

    for musicId, name in lang.Music.items():

        if 'title' not in musicId:
            continue

        similarity = fuzz.ratio(song.lower(), name.lower())
        if similarity >= maxFuzz:
            maxFuzz = similarity
            bestMatch = musicId
            
    for music in masterdata.Music:
        
        similarity = fuzz.ratio(song.lower(), music['id'].lower())
        if similarity >= maxFuzz:
            maxFuzz = similarity
            bestMatch = music
            
        elif music['titleLangId'] == bestMatch:
            bestMatch = music
            
    print(f"Best match for '{song}' is '{bestMatch["id"]}' with similarity {maxFuzz}%")
    
    return bestMatch['id'], bestMatch