from Card.Card import Card
from Card.Skill import Skill
from Score import Score, findSongByName

from glob import glob
import os
import json
import itertools
import re
import numpy as np
import time
from tqdm import tqdm
import math

def recursiveSearch(json_obj, target_key, addDict):
    if type(json_obj) is list:
        for item in json_obj:
            recursiveSearch(item, target_key, addDict)
            
    elif type(json_obj) is dict:
        for key, value in json_obj.items():
            if key == target_key:
                title = value['1'].replace('la-generated-', '').replace('.1-description', '')
                try:
                    sub = value.get('1000', None)
                    
                    if title == 'live_passive_skill-card-00001-4-cmmn-0000-00':
                        print(f"Found special case for title: {title}, sub: {sub}")
                    addDict[title] = re.sub(r"\[/?.+\]", "", sub) if sub else None
                except Exception as e:
                    pass
                    # print(f"Error processing title: {title}, sub: {sub}, error: {e}")
            else:
                recursiveSearch(value, target_key, addDict)

translationPath = 'master_data/lang/LangCard_Eng.json'

langSubDict = {}

with open(translationPath, 'r', encoding='utf-8') as f:
    json_data = json.load(f)
    
    recursiveSearch(json_data['Lang'], 'data', langSubDict)
    
characterPath = 'master_data/json/Character.json'

characterDict = {}

with open(characterPath, 'r', encoding='utf-8') as f:
    character_data = json.load(f)
    for character in character_data:
        characterDict[character['id']] = character['nameEng']

master_data_path = 'master_data/json'

cardData = os.path.join(master_data_path, 'Card.json')
with open(cardData, 'r', encoding='utf-8') as f:
    cards = json.load(f)
    
cardObjects = []
    
for card in cards:
    card_obj = Card()
    card_obj.initByDict(card)
    card_obj.card_name = langSubDict.get(card['nameLangId'], None)
    card_obj.character_name = characterDict.get(card['characterId'], None)
    # print(f"Card ID: {card_obj.card_id}, Rarity: {card_obj.card_rarity}, Type: {card_obj.card_type}")
    
    # if card_obj.active_skill:
    #     print(card_obj.active_skill)
    
    if card_obj.card_rarity != 'CARD_RARITY_RARITY_5':
        continue
        
    cardObjects.append(card_obj)
        
song = 'maware setsugetsuka'
diff = 'expert'

bestMatch = findSongByName(song)
beatmapPath = f'beatmaps/Resources/chart_{bestMatch}_{diff}.sus'

with open(beatmapPath, 'r') as f:
    content = f.readlines()
    
score = Score(content)
score.parse()
score.defineNotes()
score.addRealTime()
score.addCombo()
score.playableNotes.sort(key=lambda note: note.beat)

filtered = []

skillSet = set()

for card in cardObjects:
    if str(card.active_skill) in skillSet:
        continue
    
    skillSet.add(str(card.active_skill))
    filtered.append(card)

print(len(filtered), "cards loaded.")
combinations = itertools.combinations(filtered, 5)

maxWeight = 0
characterCombination = []

for combo in tqdm(combinations, total=math.comb(len(filtered), 5), desc="Evaluating combinations"):
    start = time.time()
    arr = np.maximum.reduce([card.active_skill.applyToChart(score.playableNotes) for card in combo])
    
    total = np.sum(arr)
    
    if total > maxWeight:
        maxWeight = total
        
        characterArray = [f"{card.character_name} ({card.card_name}) {card.active_skill}" for card in combo]
        
        print(f"New max weight: {maxWeight:.2f}")
        for character in characterArray:
            print(character)
        
        characterCombination = characterArray
    
# print(f"Total combinations of 5 cards: {len(combinations)}")

# selectedCard = cardObjects[32]

# print(selectedCard.card_id, selectedCard.card_rarity, selectedCard.card_type)
# print(selectedCard.active_skill)
# noteWeights = selectedCard.active_skill.applyToChart(score.playableNotes)

# print(f"Note Weights: {noteWeights}")