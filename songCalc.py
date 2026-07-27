import json
import numpy as np
import itertools

def main():
    
    power = 188222
    multiplier = 1.06
    
    supportSkill = SupportSkill(multiplier=1.1, duration=11)
    
    activeSkills = [
        ActiveSkill(0.9, 11, 30, 0.55),
        ActiveSkill(1.1, 9, 27, 0.46),
        ActiveSkill(1.0, 7, 19, 0.46),
        ActiveSkill(0.9, 6, 15, 0.46),
        ActiveSkill(0.55, 10, 24, 0.55)
    ]
    
    with open('music_meta.json', 'r') as f:
        musicMeta = json.load(f)
        
    song = searchMusicMeta(musicMeta, "Supernova", "expert")
    
    bestPermutation = None
    bestScore = 0
    
    for permutation in itertools.permutations(activeSkills):
    
        baseNote, maxScore = calcScore(song, power, supportSkill, permutation)
        
        if maxScore > bestScore:
            bestScore = maxScore
            bestPermutation = permutation
            
            print(f"New best score: {bestScore:.2f} with permutation: {[str(skill) for skill in bestPermutation]}")
            
    print(f"Best permutation:")
    print(f"Max Score: {bestScore:.2f}")
    for skill in bestPermutation:
        print(skill)
    
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