import json
import numpy as np
import itertools
import matplotlib.pyplot as plt
import pandas as pd
import random
from tqdm import tqdm

def main():
    
    power = 201046
    multiplier = 1.06

    activeSkills = [
        (1.2, 8, 23, 0.55),
        (1.1, 11, 30, 0.55),
        (1.2, 7, 20, 0.46),
        (1.1, 6, 15, 0.46),
        (1.3, 9, 27, 0.46)
    ]
    
    activeSkills = [ActiveSkill(multiplier=s[0], duration=s[1], cooldown=s[2], activation_chance=s[3], cooldownReduction=0.12) for s in activeSkills]
    
    activeSkills = sorted(activeSkills, key=lambda x: x.multiplier, reverse=True)
    
    supportSkills = [
        [1.45, 11],
        [1.15, 14],
        [1.6, 10],
        [1.35, 12],
        [1.45, 10]
    ]
    
    supportSkill = [SupportSkill(multiplier=s[0], duration=s[1]) for s in supportSkills]
    
    with open('music_meta.json', 'r') as f:
        musicMeta = json.load(f)
        
    for diff in ['expert']:
        song = searchMusicMeta(musicMeta, "Supernova", diff)
        # print(f"Calculating best permutation for song: {song['title']} ({diff})")
        
        bestPermutation = None
        bestScore = 0
        
        scores = []
        
        for permutation in itertools.permutations(supportSkill, 5):
        
            maxScore = calcScore(song, power, permutation, activeSkills)
            scores.append(maxScore)
            
            if maxScore > bestScore:
                bestScore = maxScore
                bestPermutation = permutation
                
                # print(f"New best score: {bestScore:.2f} with permutation: {[str(skill) for skill in bestPermutation]}")
                
        # print(f"Best permutation for {diff}: {[str(skill) for skill in bestPermutation]}")
        print(f"Percentage: {(bestScore) * 100:.2f}%")
        for skill in bestPermutation:
            print(skill)
        
        # outputScore(song, bestPermutation, activeSkills, f'output_{song["title"]}_{diff}.xlsx')
        
    # graphScore(song, power, bestPermutation, activeSkills)
    # graphRandom(song, bestPermutation, activeSkills, seed=32, trials=1e4)
    graphRandom_GPU(song, bestPermutation, activeSkills, seed=32, trials=1e8, batch_size=100000)

def graphScore(song, power, supportSkill, activeSkills):
    
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    
    plt.style.use('dark_background')
    
    fig, ax = plt.subplots(figsize=(10, 6))
    colormap = plt.get_cmap('viridis')
    
    fig.colorbar(cm.ScalarMappable(cmap=colormap), ax=ax, label='Weight Multiplier')
    
    card_colors = plt.cm.Set2.colors
    
    perSecondWeights = [0]
    
    currentSecond = 0
    secondWeight = 0
    
    for note in song['notes']:
        second = int(note[0])
        
        while second > currentSecond:
            perSecondWeights.append(0)
            currentSecond += 1
            
        perSecondWeights[second] += note[1]
        
    heatmapBars = []
    heatmapColors = []
    
    minVal = min(perSecondWeights) if perSecondWeights else 0
    maxVal = max(perSecondWeights) if perSecondWeights else 1

    for second, weight in enumerate(perSecondWeights):
        norm_val = (weight - minVal) / (maxVal - minVal) if maxVal > minVal else 0
        color = colormap(norm_val)
        
        heatmapBars.append((second, 1))
        heatmapColors.append(color)
        
    ax.broken_barh(heatmapBars, (7.5, 1), facecolors=heatmapColors, alpha=0.8, label='Expected Weight per Second')
        
    for i, skill in enumerate(activeSkills[::-1]): ## start with last first because we want the first skill to overwrite
        bars = []
        for start in np.arange(skill.cooldown, len(perSecondWeights), skill.cooldown):
            bars.append((start, skill.duration))
            
        card_color = card_colors[activeSkills.index(skill) % len(card_colors)]
        
        ax.broken_barh(bars, (i + 0.5, 0.7), facecolors=card_color, alpha=1.0, label=str(skill))
        ax.broken_barh(bars, (7.5, 0.6), facecolors=card_color, alpha=1.0, label='Skill Overlap')
        
    bars = []
    for i, support in enumerate(song['supportSkills']):
        bars.append((support, supportSkill[i].duration))
            
    ax.broken_barh(bars, (7.5, 0.3), facecolors='lightgray', alpha=0.7, label='Support Skill')
        
    ax.grid(True, axis='x', linestyle='--', alpha=0.5)
    
    tickMarks = ['', 'Skill 5', 'Skill 4', 'Skill 3', 'Skill 2', 'Skill 1', 'Skill Overlap', 'Support Skill', 'Weight Heatmap']
    ax.set_yticks(range(len(tickMarks)))
    ax.set_yticklabels(tickMarks)
    
    ax.set_xlabel('Time (seconds)')
    ax.set_ylabel('Skill / Weight')
    ax.set_title(f"Skill Proc Windows and Expected Weight for '{song['title']}'")
    ax.set_xlim(0, len(perSecondWeights) + 1)
    ax.set_ylim(0, len(tickMarks))
    
    plt.show()

def graphRandom(song, supportSkills, activeSkills, seed=32, trials=1e6):
    supportWeights = np.array(generateSupportWeights(supportSkills, song['notes'], song['supportSkills']))
    noteWeights = np.array([note[1] for note in song['notes']])
    
    skills = []
    scores = []
    skill_counts = []
    
    for skill in activeSkills:
        skillWeights, skill_procs = processSkillProcs(song['notes'], skill)
        skill_counts.append(int(skill_procs))
        
        skills.append(skillWeights)
    
    random.seed(seed)
        
    for trial in tqdm(range(int(trials)), desc="Simulating Random Skill Procs"):
        
        baseSkill = np.zeros(len(song['notes']))
        
        for i, procs in enumerate(skill_counts):
            proc_mask = np.random.rand(procs) < activeSkills[i].activation_chance
            mask = np.isin(skills[i][:, 1], np.where(proc_mask)[0] + 1)
            skill = np.where(mask, skills[i][:, 0], 0)
            
            baseSkill = np.maximum(baseSkill, skill)
            
        skillWeights = np.multiply(baseSkill, supportWeights)
        score = np.sum(noteWeights * skillWeights)
        
        scores.append(score / song['base_weight'])
        
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(scores, bins=30, color='skyblue', edgecolor='black', density=True)
    ax.set_xlabel('Score')
    ax.set_ylabel('Frequency')
    ax.set_title(f'Distribution of Scores for {song["title"]} with Random Skill Procs')
    plt.show()
    
import torch
import numpy as np
import matplotlib.pyplot as plt

def graphRandom_GPU(song, supportSkills, activeSkills, seed=32, trials=1e6, batch_size=100_000):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.manual_seed(seed)
    
    # 1. Base Song Vectors
    supportWeights = torch.tensor(
        generateSupportWeights(supportSkills, song['notes'], song['supportSkills']), 
        dtype=torch.float32, device=device
    )
    noteWeights = torch.tensor([note[1] for note in song['notes']], dtype=torch.float32, device=device)
    combined_weights = noteWeights * supportWeights  # Shape: (N,)
    base_weight = float(song['base_weight'])
    
    num_notes = len(song['notes'])
    num_skills = len(activeSkills)

    # 2. Extract CPU Pre-processing
    skills = []
    skill_counts = []
    chances = []
    
    for skill in activeSkills:
        skillWeights, skill_procs = processSkillProcs(song['notes'], skill)
        skills.append(skillWeights)
        skill_counts.append(int(skill_procs))
        chances.append(float(skill.activation_chance))

    # 3. Create a compact Note -> Proc ID matrix (Shape: 5, N)
    # and Note -> Skill Multiplier matrix (Shape: 5, N)
    proc_id_map = torch.zeros((num_skills, num_notes), dtype=torch.long, device=device)
    multiplier_map = torch.zeros((num_skills, num_notes), dtype=torch.float32, device=device)
    
    # We will flatten all proc probabilities into a single flat array
    # Index 0 = "No Proc" (Always 0 multiplier)
    flat_chances = [0.0]
    proc_offset = 1

    for i in range(num_skills):
        procs = skill_counts[i]
        proc_ids = skills[i][:, 1]    # 1..P for this skill
        multipliers = skills[i][:, 0] # Skill mult
        
        # Shift proc IDs so every proc across ALL skills gets a globally unique index
        global_ids = np.where(proc_ids > 0, proc_ids + proc_offset - 1, 0)
        
        proc_id_map[i] = torch.tensor(global_ids, dtype=torch.long, device=device)
        multiplier_map[i] = torch.tensor(multipliers, dtype=torch.float32, device=device)
        
        # Store chances for these procs
        flat_chances.extend([chances[i]] * procs)
        proc_offset += procs

    total_unique_procs = len(flat_chances)
    chances_tensor = torch.tensor(flat_chances, dtype=torch.float32, device=device) # Shape: (Total_Procs + 1,)

    # 4. Memory-efficient Batched GPU Execution Loop
    scores = []
    total_trials = int(trials)
    num_batches = (total_trials + batch_size - 1) // batch_size

    for _ in tqdm(range(num_batches), desc="vibe coded GPU go brrrrrrr"):
        cur_batch = min(batch_size, total_trials - len(scores) * batch_size)
        
        # Roll random floats for all unique procs across the batch
        # Shape: (Batch_Size, Total_Procs + 1)
        rolls = torch.rand((cur_batch, total_unique_procs), device=device)
        rolls[:, 0] = 1.0  # Proc 0 (no proc) always fails activation test
        
        # Boolean success mask -> Float (1.0 if proc fired, 0.0 if failed)
        # Shape: (Batch_Size, Total_Procs + 1)
        proc_success = (rolls < chances_tensor).float()
        
        # Index into proc_success using proc_id_map -> Shape: (Batch_Size, 5, N)
        # This checks if the specific proc active at note N succeeded in trial B
        active_mask = proc_success[:, proc_id_map]  
        
        # Multiply by skill multiplier -> Shape: (Batch_Size, 5, N)
        active_skill_weights = active_mask * multiplier_map.unsqueeze(0)
        
        # Max active skill multiplier across 5 cards -> Shape: (Batch_Size, N)
        baseSkill, _ = torch.max(active_skill_weights, dim=1)
        
        # Sum score ratio across notes -> Shape: (Batch_Size,)
        batch_scores = torch.sum(baseSkill * combined_weights.unsqueeze(0), dim=1) / base_weight
        
        scores.append(batch_scores.cpu())

    max_proc_success = torch.ones((1, total_unique_procs), dtype=torch.float32, device=device)
    max_proc_success[:, 0] = 0.0  # Proc 0 (no proc) is 0

    # Index map: (1, 5, N)
    max_active_mask = max_proc_success[:, proc_id_map]
    max_active_weights = max_active_mask * multiplier_map.unsqueeze(0)
    
    # Max active skill multiplier across 5 cards at each note
    max_baseSkill, _ = torch.max(max_active_weights, dim=1)
    
    # Calculate scalar max score ratio
    maxScore = (torch.sum(max_baseSkill * combined_weights.unsqueeze(0), dim=1) / base_weight).item()
    
    # 5. Concatenate & Plot
    final_scores = torch.cat(scores, dim=0).numpy()

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(final_scores, bins=30, color='skyblue', edgecolor='black')
    ax.set_xlabel('Score')
    ax.set_ylabel('Frequency')
    ax.set_title(f'Distribution of Scores for {song["title"]} ({total_trials:,} trials)')
    
    percentile_95 = np.percentile(final_scores, 95)
    percentile_99 = np.percentile(final_scores, 99)
    percentile_99_9 = np.percentile(final_scores, 99.9)
    maxScoreCount = np.sum(final_scores == maxScore)
    
    print(f"95th Percentile Score: {percentile_95:.5f}")
    print(f"99th Percentile Score: {percentile_99:.5f}")
    print(f"99.9th Percentile Score: {percentile_99_9:.5f}")
    print(f"Maximum Score: {maxScore:.5f}")
    print(f"Percentage of Max Score: {maxScoreCount} / {len(final_scores):,}")
    
    plt.show()

    return final_scores

def outputScore(song, supportSkills, activeSkills, output):
    supportWeights = np.array(generateSupportWeights(supportSkills, song['notes'], song['supportSkills']))
        
    skillWeights = np.array([processSkill(song['notes'], skill) for skill in activeSkills])
    filteredSkillWeights = np.max(skillWeights, axis=0)
    
    skillWeights = np.multiply(filteredSkillWeights, supportWeights)
    # print(filteredSkillWeights)
    
    calcScore = 0
    
    outputList = []
    
    for i, note in enumerate(song['notes']):
        weight = note[1]
        calcScore += weight * skillWeights[i]
        
        outputList.append([
            i + 1,
            weight,
            supportWeights[i],
            filteredSkillWeights[i],
            skillWeights[i],
            weight * skillWeights[i],
            calcScore
        ])
        
    df = pd.DataFrame(outputList, columns=['Note', 'Note Weight', 'Support Weight', 'Skill Weight', 'Total Weight', 'Note Value', 'Cumulative Score'])
    df.to_excel(output, index=False)

def calcScore(song, power, supportSkills, activeSkills):
    supportWeights = np.array(generateSupportWeights(supportSkills, song['notes'], song['supportSkills']))
    
    skillWeights = np.array([processSkill(song['notes'], skill) for skill in activeSkills])
    filteredSkillWeights = np.max(skillWeights, axis=0)
    
    skillWeights = np.multiply(filteredSkillWeights, supportWeights)
    # print(filteredSkillWeights)
    
    calcScore = 0
    
    for i, note in enumerate(song['notes']):
        weight = note[1]
        calcScore += weight * skillWeights[i]
        
    return calcScore / song['base_weight']
        
    calcScore = calcScore / song['base_weight']
    
    difficultyMultiplier = 1 + (song['difficultyLevel'] - 5) * (song['liveScoreCoefficientPermil'] / 1000)
    
    baseNote = 1000 / song['base_weight'] * difficultyMultiplier * 2.3 * power
    maxScore = calcScore * difficultyMultiplier * 2.3 * power
        
    return baseNote, maxScore

class ActiveSkill():
    def __init__(self, multiplier, duration, cooldown, activation_chance, cooldownReduction=0):
        self.multiplier = multiplier
        self.duration = duration
        self.cooldown = cooldown
        self.activation_chance = activation_chance * 1.3
        
        cooldownReduction = min(max(cooldownReduction, 0), 1)
        self.cooldown *= (1 - cooldownReduction)
        
    def __str__(self):
        return f"ActiveSkill(multiplier={self.multiplier:.2f}, duration={self.duration}, cooldown={self.cooldown}, activation_chance={self.activation_chance:.2f}%)"
        
class SupportSkill():
    
    def __init__(self, multiplier, duration):
        self.multiplier = multiplier
        self.duration = duration
        
    def __str__(self):
        return f"SupportSkill(multiplier={self.multiplier:.2f}, duration={self.duration})"

def searchMusicMeta(musicMeta, songName, difficulty):
    for song in musicMeta:
        if song['title'].lower() == songName.lower() and song['difficulty'].lower() == difficulty.lower():
            return song
    return None

def generateSupportWeights(supportSkills, notes, supportSkillTimings):
    
    skillIdx = 0
    startTime = supportSkillTimings[skillIdx]
    
    supportWeights = [1] * len(notes)
    
    for j, support in enumerate(supportSkills):
        startTime = supportSkillTimings[j]
        endTime = startTime + support.duration
        
        for i, note in enumerate(notes):
            
            time = note[0]
            
            if time >= startTime and time <= endTime:
                
                supportWeights[i] = 1 + supportSkills[j].multiplier
                
    return supportWeights
            
def processSkill(notes, skill, filter=[]):
    
    skillWeightList = [0] * len(notes)
    
    nextProc = skill.cooldown
    skillIdx = 1
    
    for i, note in enumerate(notes):
        
        time, weight = note[0], note[1]
            
        if time >= nextProc and time <= nextProc + skill.duration:
            
            ## Yay gambling
            if skillIdx <= len(filter) and filter[skillIdx-1]:
                skillWeightList[i] = 0
                continue
            
            skillWeightList[i] = skill.multiplier
            
        elif time > nextProc + skill.duration:
            nextProc += skill.cooldown
            skillIdx += 1
            
            
    return skillWeightList

def processSkillProcs(notes, skill, start=1):
    
    nextProc = skill.cooldown

    skillIdx = start
    skillProcs = max(note[0] for note in notes) // skill.cooldown
    
    skillWeightList = [[0, 0] for _ in range(len(notes))]
    
    for i, note in enumerate(notes):
        
        time, weight = note[0], note[1]
            
        if time >= nextProc and time <= nextProc + skill.duration:
            
            skillWeightList[i] = [skill.multiplier, int(skillIdx)]
            
        elif time > nextProc + skill.duration:
            nextProc += skill.cooldown
            skillIdx += 1
            
    skillWeightList = np.array(skillWeightList)
    return skillWeightList, skillProcs

def getFirstNonZero(arr):
    stacked = np.vstack(arr)
    mask = stacked != 0
    
    first_nonzero_idx = np.argmax(mask, axis=0)
    
    output = stacked[first_nonzero_idx, np.arange(stacked.shape[1])]
    
    output[~mask.any(axis=0)] = 0
    
    return output

if __name__ == '__main__':
    main()