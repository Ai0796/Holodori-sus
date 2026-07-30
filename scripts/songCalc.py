import json
import numpy as np
import itertools

def main():
    
    power = 201046
    multiplier = 1.06
    
    supportSkill = SupportSkill(multiplier=1.1, duration=11)

    activeSkills = [
        ActiveSkill(1.0, 10, 29, 0.55),
        ActiveSkill(0.9, 6, 15, 0.55),
        ActiveSkill(1.1, 9, 27, 0.55),
        ActiveSkill(0.9, 11, 30, 0.55),
        ActiveSkill(0.55, 10, 24, 0.55)
    ]
    
    with open('music_meta.json', 'r') as f:
        musicMeta = json.load(f)
        
    for diff in ['easy', 'normal', 'hard', 'expert']:
        song = searchMusicMeta(musicMeta, "Wicked feat. Mori Calliope", diff)
        # print(f"Calculating best permutation for song: {song['title']} ({diff})")
        
        bestPermutation = None
        bestScore = 0
        
        for permutation in itertools.permutations(activeSkills):
        
            baseNote, maxScore = calcScore(song, power, supportSkill, permutation)
            
            if maxScore > bestScore:
                bestScore = maxScore
                bestPermutation = permutation
                
                # print(f"New best score: {bestScore:.2f} with permutation: {[str(skill) for skill in bestPermutation]}")
                
        print(f"Best permutation for {diff}:")
        print(f"Max Score: {bestScore:.2f}")
        print(f'Base Note: {baseNote:.2f}')
        for skill in bestPermutation:
            print(skill)
            
    graphScore(song, power, supportSkill, bestPermutation)

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
        
        while second != currentSecond:
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
        for start in range(skill.cooldown, len(perSecondWeights), skill.cooldown):
            bars.append((start, skill.duration))
            
        card_color = card_colors[activeSkills.index(skill) % len(card_colors)]
        
        ax.broken_barh(bars, (i + 0.5, 0.7), facecolors=card_color, alpha=1.0, label=str(skill))
        ax.broken_barh(bars, (7.5, 0.6), facecolors=card_color, alpha=1.0, label='Skill Overlap')
        
    bars = []
    for support in song['supportSkills']:
        bars.append((support, supportSkill.duration))
            
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

def calcScore(song, power, supportSkills, activeSkills):
    generateSupportWeights(supportSkills, song['notes'], song['supportSkills'])
    
    skillWeights = [processSkill(song['notes'], skill) for skill in activeSkills]
    filteredSkillWeights = getFirstNonZero(skillWeights)
    
    calcScore = 0
    
    for i, note in enumerate(song['notes']):
        weight = note[1]
        calcScore += weight * (1 + filteredSkillWeights[i])
        
    calcScore = calcScore / song['base_weight']
    
    difficultyMultiplier = 1 + (song['difficultyLevel'] - 5) * (song['liveScoreCoefficientPermil'] / 1000)
    
    baseNote = 1000 / song['base_weight'] * difficultyMultiplier * 2.3 * power
    maxScore = calcScore * difficultyMultiplier * 2.3 * power
        
    return baseNote, maxScore

class ActiveSkill():
    def __init__(self, multiplier, duration, cooldown, activation_chance):
        self.multiplier = multiplier
        self.duration = duration
        self.cooldown = cooldown
        self.activation_chance = activation_chance
        
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

def generateSupportWeights(supportSkill, notes, supportSkillTimings):
    
    skillIdx = 0
    startTime = supportSkillTimings[skillIdx]
    
    idx = 0
    
    for note in notes:
        
        time = note[0]
        
        if not startTime or time < startTime:
            note.append(1)
        
        elif time >= startTime and time <= startTime + supportSkill.duration:
            
            note.append(1 + supportSkill.multiplier)

        elif note[0] > startTime + supportSkill.duration:
            skillIdx += 1
            startTime = supportSkillTimings[skillIdx] if skillIdx < len(supportSkillTimings) else None
            
            note.append(1)
            
def processSkill(notes, skill, filter=[]):
    
    skillWeightList = []
    
    nextProc = skill.cooldown
    skillIdx = 1
    
    for note in notes:
        
        time, weight, support = note[0], note[1], note[2]
        
        if time < nextProc:
            skillWeightList.append(0)
            
        elif time >= nextProc and time <= nextProc + skill.duration:
            
            ## Yay gambling
            if skillIdx <= len(filter) and filter[skillIdx-1]:
                skillWeightList.append(0)
                continue
            
            skillWeightList.append(skill.multiplier * support)
            
        else:
            nextProc += skill.cooldown
            skillWeightList.append(0)
            skillIdx += 1
            
    return skillWeightList

def getFirstNonZero(arr):
    stacked = np.vstack(arr)
    mask = stacked != 0
    
    first_nonzero_idx = np.argmax(mask, axis=0)
    
    output = stacked[first_nonzero_idx, np.arange(stacked.shape[1])]
    
    output[~mask.any(axis=0)] = 0
    
    return output

if __name__ == '__main__':
    main()