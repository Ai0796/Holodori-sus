from dataclasses import dataclass
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
import json

def searchMusicMeta(songName, difficulty):
    
    with open('music_meta.json', 'r') as f:
        musicMeta = json.load(f)
    
    for song in musicMeta:
        if song['title'].lower() == songName.lower() and song['difficulty'].lower() == difficulty.lower():
            return song
    return None

@dataclass
class Note:
    time_offset: float
    weight: float
    real_weight: float = 0.0

lockedChar = 'card-00006-5-uniq-0007-00' ## There will always be a required card on the team
    
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
        
song = 'supernova'
diff = 'expert'

bestMatch = searchMusicMeta(song, diff)

playableNotes = []
supportSkills = []

for note in bestMatch['notes']:
    playableNotes.append(Note(time_offset=note[0], weight=note[1], real_weight=note[1]))
    
for note in bestMatch['supportSkills']:
    supportSkills.append(Note(time_offset=note, weight=0))
    
supportSkillTimes = [note.time_offset for note in supportSkills]

totalWeight = bestMatch['base_weight']

skillSet = set()
skillMap = defaultdict(list)

characters = []

for card in cardObjects:
    
    key = str(card.active_skill) + str(card.special_skill)
    
    if key in skillSet:
        skillMap[key].append(card)
        continue
    
    skillSet.add(key)
    filtered.append(card)

print(len(filtered), "cards loaded.")
# exit()
combinations = itertools.combinations(filtered, 4)

maxWeight = 0
worstWeight = float('inf')
characterCombination = []

comboWeights = []
comboExpected = []

# score.weightArraySupport(supportSkill['Length'], supportSkill['Boost'])

bestCombo = None
bestPerm = 0

PERMUTATIONS = list(itertools.permutations([1, 2, 3, 4, 5], 5))

import torch

# Target RTX 3090
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Targeting GPU: {torch.cuda.get_device_name(0)}")

# Enable PyTorch Benchmark for maximum CUDA graph speed
torch.backends.cudnn.benchmark = True

# 1. PRE-COMPUTE ALL CARD SKILLS INTO GPU TENSORS
all_cards = [lockedCardObj] + list(filtered)
card_id_to_idx = {card.card_id: i for i, card in enumerate(all_cards)}
num_cards = len(all_cards)
num_notes = len(playableNotes)

active_tensor = torch.zeros((num_cards, num_notes), dtype=torch.float32, device=device)
support_tensor = torch.zeros((num_cards, 5, num_notes), dtype=torch.float32, device=device)

for card in all_cards:
    c_idx = card_id_to_idx[card.card_id]
    
    # Pre-calculate active skill array
    act = card.active_skill.applyToChart(playableNotes)
    active_tensor[c_idx] = torch.tensor(act, dtype=torch.float32, device=device)
    
    # Pre-calculate support skill multipliers
    sup = card.special_skill.applyToChart(playableNotes, supportSkillTimes)
    for p in range(1, 6):
        mult = np.where(sup[:, 0] == p, sup[:, 1], 1.0)
        support_tensor[c_idx, p - 1] = torch.tensor(mult, dtype=torch.float32, device=device)

# 2. PERMUTATIONS TENSOR (120, 5) ON GPU
PERMUTATIONS = list(itertools.permutations([1, 2, 3, 4, 5], 5))
perm_tensor = torch.tensor(PERMUTATIONS, device=device) - 1  # 0-indexed for CUDA

# 3. BUILD ALL COMBINATIONS MATRIX DIRECTLY ON GPU (341,055 x 5)
filtered_indices = [card_id_to_idx[c.card_id] for c in filtered]
locked_idx = card_id_to_idx[lockedCardObj.card_id]

# Generate raw tuples of indices
raw_combos = list(itertools.combinations(filtered_indices, 4))
total_combos = len(raw_combos)

combo_matrix = torch.zeros((total_combos, 5), dtype=torch.long, device=device)
combo_matrix[:, 0] = locked_idx
combo_matrix[:, 1:] = torch.tensor(raw_combos, dtype=torch.long, device=device)

# Pre-allocate output arrays in VRAM to store best scores/perms for each combo
best_scores_per_combo = torch.zeros(total_combos, dtype=torch.float32, device=device)
best_perms_per_combo = torch.zeros(total_combos, dtype=torch.long, device=device)

# import os
# os.environ['PYTORCH_JIT'] = '0'

# 4. FUSED JIT CUDA KERNEL FOR RTX 3090 L2 CACHE
@torch.jit.script
def evaluate_batch_fused(b_act, b_sup, perm_tensor):
    """
    b_act: (B, 5, N)
    b_sup: (B, 5, 5, N)
    perm_tensor: (120, 5)
    
    Evaluates 120 permutations sequentially in CUDA registers to avoid multi-GB VRAM allocations.
    """
    B = b_act.shape[0]
    
    # Track max scores (use -1.0 so 0.0 scores record perm index 0 properly)
    best_scores = torch.full((B,), -1.0, device=b_act.device, dtype=torch.float32)
    best_perms = torch.zeros(B, device=b_act.device, dtype=torch.long)
    
    # Max active skill across the 5 cards in team at each note N
    # Resulting shape: (B, N)
    max_act = torch.maximum(b_act[:, 0, :], b_act[:, 1, :])
    max_act = torch.maximum(max_act, b_act[:, 2, :])
    max_act = torch.maximum(max_act, b_act[:, 3, :])
    max_act = torch.maximum(max_act, b_act[:, 4, :])
    
    for p_idx in range(120):
        # Extract support timing mappings for this permutation
        p0 = perm_tensor[p_idx, 0]
        p1 = perm_tensor[p_idx, 1]
        p2 = perm_tensor[p_idx, 2]
        p3 = perm_tensor[p_idx, 3]
        p4 = perm_tensor[p_idx, 4]
        
        # Max active support multiplier across the 5 cards for timing windows p0..p4
        # Defaults to 1.0 when no support skill is active
        sup_comb = torch.maximum(b_sup[:, 0, p0, :], b_sup[:, 1, p1, :])
        sup_comb = torch.maximum(sup_comb, b_sup[:, 2, p2, :])
        sup_comb = torch.maximum(sup_comb, b_sup[:, 3, p3, :])
        sup_comb = torch.maximum(sup_comb, b_sup[:, 4, p4, :])
        
        # Element-wise product: (real_weight * active_mult) * support_mult
        note_scores = max_act * sup_comb
        
        # Sum across notes and divide by base_weight -> Shape (B,)
        perm_totals = torch.sum(note_scores, dim=1)
        
        # Update best score and perm index in-place
        mask = perm_totals > best_scores
        best_scores = torch.where(mask, perm_totals, best_scores)
        best_perms = torch.where(mask, p_idx, best_perms)
        
    return best_scores, best_perms

# 5. HIGH-SPEED BATCHED EXECUTION
# 2048 keeps active batch memory safely inside the 3090's L2 Cache
BATCH_SIZE = 2048

for start_idx in tqdm(range(0, total_combos, BATCH_SIZE), desc="GPU go brrrrr"):
    end_idx = min(start_idx + BATCH_SIZE, total_combos)
    batch_combos = combo_matrix[start_idx:end_idx]
    
    # Slice tensors directly on GPU
    b_act = active_tensor[batch_combos] 
    b_sup = support_tensor[batch_combos]
    
    # Run fused CUDA calculation
    max_scores, best_perms = evaluate_batch_fused(b_act, b_sup, perm_tensor)
    
    # Store directly in GPU buffer
    best_scores_per_combo[start_idx:end_idx] = max_scores
    best_perms_per_combo[start_idx:end_idx] = best_perms

# 6. EXTRACT BEST & WORST RESULTS (SINGLE CPU SYNC AT THE VERY END)
max_val, max_idx = torch.max(best_scores_per_combo, dim=0)
min_val, min_idx = torch.min(best_scores_per_combo, dim=0)

maxWeight = max_val.item()
worstWeight = min_val.item()

best_combo_card_indices = combo_matrix[max_idx].tolist()
best_perm_index = best_perms_per_combo[max_idx].item()
bestPerm = PERMUTATIONS[best_perm_index]

# Map integer indices back to Card objects
locked_card_result = all_cards[best_combo_card_indices[0]]
bestCombo = [all_cards[idx] for idx in best_combo_card_indices[1:]]

# PRINT FINAL RESULTS
print("\n" + "="*50)
print(f"Worst weight: {worstWeight:.2f}")
print(f"Best weight: {maxWeight:.2f} ({maxWeight/totalWeight:.2%} of total weight)")
print(f"Locked card: {locked_card_result.character_name} ({locked_card_result.card_name})")

bestCombo = [locked_card_result] + bestCombo  # Include locked card in the final output

import re

supportSkill = []

for cardNum, i in enumerate(bestPerm):
    card = bestCombo[i - 1]  # Adjust for 0-indexed permutation
    print(f"Card {cardNum + 1}: {card.character_name} ({card.card_name})")
    print('\tActive: ', re.sub(r'\[/?highlight\]', '', str(card.active_skill)))
    print('\tSpecial: ', re.sub(r'\[/?highlight\]', '', str(card.special_skill)))
    
    key = str(card.active_skill) + str(card.special_skill)
    if key in skillMap:
        for alternative in skillMap[key]:
            print(f"   Alternative: {alternative.character_name} ({alternative.card_name})")
            
    supportSkill.append(card.special_skill.getDuration())

print(f"Best permutation: {bestPerm}")
print("="*50)

# exit()
        
import matplotlib.pyplot as plt

all_scores_cpu = best_scores_per_combo.cpu().numpy()
score_percentages = all_scores_cpu / totalWeight

plt.hist(score_percentages, bins=50, color='skyblue', edgecolor='black', alpha=0.7, label='Max Weight Distribution')

plt.xlabel('Combination Weight')
plt.ylabel('Frequency')
plt.title('Distribution of Card Combination Weights')
plt.show()