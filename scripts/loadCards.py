import random

from Card.Card import Card
from Score import Score

from scripts.findSongByName import findSongByName

import itertools
import numpy as np
import time
from tqdm import tqdm
import math
import shutil
from collections import defaultdict
import pandas as pd
import scipy.stats as stats

from lib.language import Lang
from lib.master_data import MasterData

lockedChar = 'card-00006-5-uniq-0007-00' ## There will always be a required card on the team

supportSkill = {
    'Length': 10,
    'Boost': 1.45
}
    
cardObjects = []

lockedCardObj = None

LangObj = Lang()
MasterDataObj = MasterData()

filtered = []
    
for card in MasterDataObj.Card:
    card_obj = Card(MasterDataObj, LangObj)
    card_obj.initByDict(card)
    
    if card_obj.card_rarity != 'CARD_RARITY_RARITY_5':
        continue
    
    if card_obj.card_id == lockedChar:
        lockedCardObj = card_obj
        # print(f"Locked card found: {lockedCardObj.character_name} ({lockedCardObj.card_name})")
        continue
        
    print(f"Loaded card: {card_obj.character_name} ({card_obj.card_name})")
    print(f"  Active Skill: {card_obj.active_skill}")
    cardObjects.append(card_obj)
    
# exit()
        
song = 'god knows'
diff = 'expert'

bestMatch = findSongByName(song)[0]
beatmapPath = f'beatmaps/Resources/chart_{bestMatch}_{diff}.sus'

shutil.copy(beatmapPath, f'selected/chart_{song}_{diff}.sus')

with open(beatmapPath, 'r') as f:
    content = f.readlines()
    
score = Score(content)
score.parse()
score.addRealTime()
score.addCombo()
score.weightArraySupport(supportSkill['Length'], supportSkill['Boost'])
score.playableNotes.sort(key=lambda note: note.beat)

totalWeight = 0

for note in score.playableNotes:
    totalWeight += note.real_weight

skillSet = set()
skillMap = defaultdict(list)

characters = []

for card in cardObjects:
    
    if str(card.active_skill) in skillSet:
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

secondColormap = plt.get_cmap('viridis')

minVal = 0
maxVal = max(perSecondWeights)

import matplotlib.pyplot as plt
import matplotlib.cm as cm

# Setup layout and color scheme
fig, ax = plt.subplots(figsize=(12, 6))

fig.colorbar(cm.ScalarMappable(cmap=secondColormap), ax=ax, orientation='vertical', label='Expected Weight Intensity')

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

for i, card in enumerate(bestCombo, start=0):
    bars = []
    cooldown = int(card.active_skill.cooldown / 1000)
    duration = int(card.active_skill.duration / 1000)
    
    # Calculate proc intervals
    # (Note: adjust range step logic if skill activates right at t=0 or requires trigger condition)
    for start in range(cooldown, len(perSecondWeights), cooldown):
        bars.append((start, duration))
    
    card_color = card_colors[i % len(card_colors)]
    
    # Draw skill lane at y-index i (Y = 0 to 4)
    # Height is set to 0.7 with y offset i + 0.15 for clean padding/gaps
    ax.broken_barh(bars, (i + 0.15, 0.7), facecolors=card_color, edgecolor='none', alpha=0.85)
    ax.broken_barh(bars, (6.1, 0.3), facecolors=card_color, edgecolor='none', alpha=1)
    
    card_label = f'{card.character_name} ({card.card_name})'
    
    # Use card name or fallback identifier for label
    # card_label = getattr(card, 'name', f"Card {i+1}")
    yticklabels.append(card_label)
    
ax.broken_barh(supportSkills, (5.1, 0.7), facecolors='lightgray', edgecolor='none', alpha=0.5)
ax.broken_barh(supportSkills, (6.1, 0.2), facecolors='lightgray', edgecolor='none', alpha=0.7)

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

def calculateVariance(arr, totalWeight):
    E = 0
    var = 0
    remainingProb = 1.0
    
    for skill in arr:
        if skill == 0: continue ## 0 is skipped
        
        skill[0] = skill[0] / totalWeight if totalWeight > 0 else 0
        
        prob = skill[1] * remainingProb
        remainingProb *= (1 - skill[1])
        
        E += skill[0] * prob
        var += ((skill[0] * prob) ** 2) * (prob * (1 - prob))
        
    return E, var

bestCombo = sorted(bestCombo, key=lambda card: card.active_skill.getMult(), reverse=True)

allProcced = [card.active_skill.applyToChartProbability(score.playableNotes) for card in bestCombo]

expected = 0
variance = 0

for i in range(len(allProcced[0])):
    skills = [allProcced[j][i] for j in range(len(allProcced))]
    E, var = calculateVariance(skills, totalWeight)
    
    expected += E
    variance += var
    
x = np.linspace(expected - 6 * math.sqrt(variance), expected + 6 * math.sqrt(variance), 1000)

fig, ax = plt.subplots(figsize=(12, 6))
random_samples = 1000

outputs = []

arr = np.maximum.reduce([card.active_skill.applyToChart(score.playableNotes) for card in bestCombo])

print(f"Max Weight: {np.sum(arr):.2f} / Total Weight: {totalWeight:.2f} ({np.sum(arr) / totalWeight:.2%})")
maxWeight = np.sum(arr) / totalWeight
# outputs.append(np.sum(arr) / totalWeight)

random.seed(32)
for sample in tqdm(range(random_samples)):
    arr = []
    ## different random seed for each card to simulate independent skill activations
    for card in bestCombo:
        seed = random.randint(0, 2**32 - 1)
        arr.append(card.active_skill.applyToChartRandom(score.playableNotes, random_state=seed))
        
    arr = np.maximum.reduce(arr)
    total = np.sum(arr)
    
    outputs.append(total / totalWeight)
    
outputs = sorted(outputs)

print("Highest output:", max(outputs))
for output in outputs:
    if output >= maxWeight:
        print(f"Random simulation reached max weight: {output:.9f}")
    
ax.hist(outputs, bins=300, color='skyblue', edgecolor='black', alpha=0.7)
ax.plot(x, stats.norm.pdf(x, loc=expected, scale=math.sqrt(variance)), color='red', linewidth=2, label='Normal Distribution Fit')
ax.legend()
ax.set_title(f"Distribution of Total Weight Proportion over {random_samples} Random Simulations", fontsize=14, pad=12)
ax.set_xlabel("Proportion of Total Weight (compared to song base combo weight)", fontsize=11)
ax.set_ylabel("Percentage", fontsize=11)

ax.set_yticklabels([f"{int(y / random_samples * 100)}%" for y in ax.get_yticks()])

plt.tight_layout()
plt.show()
        

# print(f"Total combinations of 5 cards: {len(combinations)}")

# selectedCard = cardObjects[32]

# print(selectedCard.card_id, selectedCard.card_rarity, selectedCard.card_type)
# print(selectedCard.active_skill)
# noteWeights = selectedCard.active_skill.applyToChart(score.playableNotes)

# print(f"Note Weights: {noteWeights}")