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
        
song = 'm0184'
diff = 'expert'

bestMatch = findSongByName(song)[0]
beatmapPath = f'beatmaps/Resources/chart_{bestMatch}_{diff}.sus'

shutil.copy(beatmapPath, f'selected/chart_{song}_{diff}.sus')

with open(beatmapPath, 'r') as f:
    content = f.readlines()
    
score = Score(content)
score.parse()
score.playableNotes.sort(key=lambda note: note.beat)

totalWeight = 0

for note in score.playableNotes:
    totalWeight += note.weight

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

supportSkillTimes = [note.time_offset for note in score.skills]

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
num_notes = len(score.playableNotes)

active_tensor = torch.zeros((num_cards, num_notes), dtype=torch.float32, device=device)
support_tensor = torch.zeros((num_cards, 5, num_notes), dtype=torch.float32, device=device)

for card in all_cards:
    c_idx = card_id_to_idx[card.card_id]
    
    # Pre-calculate active skill array
    act = card.active_skill.applyToChart(score.playableNotes)
    active_tensor[c_idx] = torch.tensor(act, dtype=torch.float32, device=device)
    
    # Pre-calculate support skill multipliers
    sup = card.special_skill.applyToChart(score.playableNotes, supportSkillTimes)
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
    
    best_scores = torch.zeros(B, device=b_act.device, dtype=torch.float32)
    best_perms = torch.zeros(B, device=b_act.device, dtype=torch.long)
    
    for p_idx in range(120):
        p0 = perm_tensor[p_idx, 0]
        p1 = perm_tensor[p_idx, 1]
        p2 = perm_tensor[p_idx, 2]
        p3 = perm_tensor[p_idx, 3]
        p4 = perm_tensor[p_idx, 4]
        
        # Multiply skills by multipliers for permutation p_idx
        s0 = b_act[:, 0, :] * b_sup[:, 0, p0, :]
        s1 = b_act[:, 1, :] * b_sup[:, 1, p1, :]
        s2 = b_act[:, 2, :] * b_sup[:, 2, p2, :]
        s3 = b_act[:, 3, :] * b_sup[:, 3, p3, :]
        s4 = b_act[:, 4, :] * b_sup[:, 4, p4, :]
        
        # Element-wise maximum across the 5 cards
        m = torch.maximum(s0, s1)
        m = torch.maximum(m, s2)
        m = torch.maximum(m, s3)
        m = torch.maximum(m, s4)
        
        # Sum across all playable notes -> Shape (B,)
        perm_totals = torch.sum(m, dim=1)
        
        # In-place tracking of max perms
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
print(f"Best weight: {maxWeight:.2f} ({maxWeight / totalWeight:.2%} of total weight)")
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