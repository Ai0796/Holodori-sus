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
import shutil
from collections import defaultdict

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

lockedChar = 'card-00039-5-uniq-0032-00' ## There will always be a required card on the team

supportSkill = {
    'Length': 10,
    'Boost': 1.45
}

with open(characterPath, 'r', encoding='utf-8') as f:
    character_data = json.load(f)
    for character in character_data:
        characterDict[character['id']] = character['nameEng']

master_data_path = 'master_data/json'

cardData = os.path.join(master_data_path, 'Card.json')
with open(cardData, 'r', encoding='utf-8') as f:
    cards = json.load(f)
    
cardObjects = []

lockedCardObj = None
    
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
    
    if card_obj.card_id == lockedChar:
        lockedCardObj = card_obj
        print(f"Locked card found: {lockedCardObj.character_name} ({lockedCardObj.card_name})")
        continue
        
    cardObjects.append(card_obj)
        
song = 'iroha step'
diff = 'expert'

bestMatch = findSongByName(song)
beatmapPath = f'beatmaps/Resources/chart_{bestMatch}_{diff}.sus'

shutil.copy(beatmapPath, f'selected/chart_{song}_{diff}.sus')

with open(beatmapPath, 'r') as f:
    content = f.readlines()
    
score = Score(content)
score.parse()
score.defineNotes()
score.addRealTime()
score.addCombo()
score.weightArraySupport(supportSkill['Length'], supportSkill['Boost'])
score.playableNotes.sort(key=lambda note: note.beat)

filtered = []

skillSet = set()
skillMap = defaultdict(list)

for card in cardObjects:
    
    if str(card.active_skill) in skillSet:
        # print(f"Duplicate skill found: {card.active_skill} for card {card.character_name} ({card.card_name})")
        skillMap[str(card.active_skill)].append(card)
        continue
    
    skillSet.add(str(card.active_skill))
    filtered.append(card)

print(len(filtered), "cards loaded.")
# exit()
combinations = itertools.combinations(filtered, 4)

maxWeight = 0
characterCombination = []

score.weightArraySupport(supportSkill['Length'], supportSkill['Boost'])

bestCombo = None

for combo in tqdm(combinations, total=math.comb(len(filtered), 4), desc="Evaluating combinations"):
    
    combo = [lockedCardObj] + list(combo)
    
    start = time.time()
    arr = np.maximum.reduce([card.active_skill.applyToChart(score.playableNotes) for card in combo])
    
    total = np.sum(arr)
    
    if total > maxWeight:
        maxWeight = total
        
        print(f"New max weight: {maxWeight:.2f}")
        for card in combo:
            print(f"{card.character_name} ({card.card_name}) {card.active_skill}")
            
            for alternatives in skillMap[str(card.active_skill)]:
                print(f"  Alternative: {alternatives.character_name} ({alternatives.card_name})")
                
        bestCombo = combo
        
        # break
        
import matplotlib.pyplot as plt

perSecondWeights = [0]

currentSecond = 0
secondWeight = 0
for note in score.playableNotes:
    second = int(note.time_offset)
    
    while second != currentSecond:
        perSecondWeights.append(0)
        currentSecond += 1
        
    perSecondWeights[second] += note.real_weight
    
print(perSecondWeights)

secondColormap = plt.get_cmap('copper')

minVal = 0
maxVal = max(perSecondWeights)

import matplotlib.pyplot as plt
import matplotlib.cm as cm

# Setup layout and color scheme
fig, ax = plt.subplots(figsize=(12, 6))

# Distinct palette for the 5 skill rows
card_colors = plt.cm.Set2.colors  # 8 soft distinct colors

# -------------------------------------------------------------
# 1. Top Bar: Total Expected Weight per Second
# -------------------------------------------------------------
heatmapBars = []
heatmapColors = []

for second, weight in enumerate(perSecondWeights):
    norm_val = (weight - minVal) / (maxVal - minVal) if maxVal > minVal else 0
    color = secondColormap(norm_val)
    
    heatmapBars.append((second, 1))
    heatmapColors.append(color)

# Place the weight heatmap at the top lane (Y = 5)
ax.broken_barh(heatmapBars, (6.1, 0.8), facecolors=heatmapColors)


# -------------------------------------------------------------
# 2. Lower 5 Bars: Skill Proc Windows
# -------------------------------------------------------------
yticklabels = []

supportSkills = []

for skill in score.skills:
    offset = skill.time_offset
    supportSkills.append((offset, supportSkill['Length']))
    
ax.broken_barh(supportSkills, (5.1, 0.7), facecolors='lightgray', edgecolor='none', alpha=0.5)

for i, card in enumerate(bestCombo, start=0):
    bars = []
    cooldown = int(card.active_skill.cooldown / 1000)
    duration = int(card.active_skill.duration / 1000)
    
    # Calculate proc intervals
    # (Note: adjust range step logic if skill activates right at t=0 or requires trigger condition)
    for start in range(cooldown, len(perSecondWeights), cooldown + duration):
        bars.append((start, duration))
    
    card_color = card_colors[i % len(card_colors)]
    
    # Draw skill lane at y-index i (Y = 0 to 4)
    # Height is set to 0.7 with y offset i + 0.15 for clean padding/gaps
    ax.broken_barh(bars, (i + 0.15, 0.7), facecolors=card_color, edgecolor='none', alpha=0.85)
    
    # Use card name or fallback identifier for label
    card_label = getattr(card, 'name', f"Card {i+1}")
    yticklabels.append(card_label)

# Append top bar label
yticklabels.append("Support Skill Window")
yticklabels.append("Expected Weight")


# -------------------------------------------------------------
# 3. Axis Formatting & Styling
# -------------------------------------------------------------
ax.set_yticks([i + 0.5 for i in range(len(bestCombo) + 2)])
ax.set_yticklabels(yticklabels)

# Add light gridlines on time ticks for readable alignment
ax.grid(True, axis='x', linestyle='--', alpha=0.5)

# Set labels and layout limits
ax.set_title(f"Skill Activation & Note Weights: {song} [{diff}]", fontsize=14, pad=12)
ax.set_xlabel("Time (seconds)", fontsize=11)
ax.set_xlim(0, len(perSecondWeights))
ax.set_ylim(0, len(bestCombo) + 2.4)

plt.tight_layout()
plt.show()
# print(f"Total combinations of 5 cards: {len(combinations)}")

# selectedCard = cardObjects[32]

# print(selectedCard.card_id, selectedCard.card_rarity, selectedCard.card_type)
# print(selectedCard.active_skill)
# noteWeights = selectedCard.active_skill.applyToChart(score.playableNotes)

# print(f"Note Weights: {noteWeights}")