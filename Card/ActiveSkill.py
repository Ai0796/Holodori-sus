import re

import json
import numpy as np

from lib.master_data import MasterData
from lib.language import Lang
import random

class ActiveSkill():
    
    def __init__(self, master_data: MasterData, lang: Lang):
        self.skill_id = None
        self.level = None
        self.skill_effect = None
        self.additional_skill_condition = None
        self.additional_skill_effect = None
        self.cooldown = None
        self.activation_chance = None
        self.duration = None
        self.description = None
        
        self.noteWeights = None
        self.skillProcs = None
        
        self.master_data = master_data
        self.lang = lang
        
    def initByName(self, skill_id):
        skills = self.master_data.LiveActiveSkillLevel
            
        for skill in skills:
            if skill['liveActiveSkillId'] == skill_id and skill['level'] == 2:
                self.initByDict(skill)
                break
    
    def initByDict(self, skill_object: dict):
        self.skill_id = skill_object.get('liveActiveSkillId', None)
        self.level = skill_object.get('level', None)
        self.skill_effect = skill_object.get('liveActiveSkillEffectGroupId', None)
        self.additional_skill_condition = skill_object.get('additionalLiveSkillTriggerGroupId', None)
        self.additional_skill_effect = skill_object.get('additionalLiveActiveSkillEffectGroupId', None)
        self.cooldown = skill_object.get('coolTimeMillisecond', None)
        self.activation_chance = skill_object.get('activationProbabilityPermilMultiply', None)
        self.duration = skill_object.get('effectDurationMillisecond', None)
        self.descriptionId = skill_object.get('descriptionLangId', None)
        self.description = self.lang.LiveActiveSkillLevel.get(self.descriptionId, None)
    
    def initByData(self, skill_id, level, skill_effect, additional_skill_condition, additional_skill_effect, cooldown, activation_chance, duration, description):
        self.skill_id = skill_id
        self.level = level
        self.skill_effect = skill_effect
        self.additional_skill_condition = additional_skill_condition
        self.additional_skill_effect = additional_skill_effect
        self.cooldown = cooldown
        self.activation_chance = activation_chance
        self.duration = duration
        self.description = description
        
    def getMult(self):
        
        skill_effect = self.skill_effect
        if self.additional_skill_effect is not None:
            skill_effect = self.additional_skill_effect
            
        mult = float(skill_effect.split('-')[-1]) / 1000.0
        
        return mult
    
    def applyToChart(self, playableNotes):
        
        if self.noteWeights is not None:
            return self.noteWeights
        
        mult = self.getMult()
        cooldown = self.getCooldown()
        duration = self.getDuration()
        probability = self.getProbability()
        
        self.noteWeights = []
        self.expectedWeights = []
        
        idx = 0
        skillStart = cooldown
        skillEnd = cooldown + duration
        
        while idx < len(playableNotes):
            note = playableNotes[idx]
            
            if note.time_offset >= skillStart and note.time_offset <= skillEnd:
                self.noteWeights.append(note.real_weight * mult)
                self.expectedWeights.append(note.real_weight * mult * probability)
                idx += 1
                continue
                
            elif note.time_offset > skillEnd:
                skillStart += cooldown
                skillEnd += cooldown
            
            self.noteWeights.append(0)
            self.expectedWeights.append(0)
            idx += 1
        
        self.noteWeights = np.array(self.noteWeights)
        self.expectedWeights = np.array(self.expectedWeights)
        return self.noteWeights
    
    def getSkillProcs(self, playableNotes):
        
        if self.skillProcs is not None:
            return self.skillProcs
        
        mult = self.getMult()
        cooldown = self.getCooldown()
        duration = self.getDuration()
        
        self.skillProcs = []
        
        idx = 0
        skillStart = cooldown
        skillEnd = cooldown + duration
        
        skillProc = 1
        
        while idx < len(playableNotes):
            note = playableNotes[idx]
            
            if (note.time_offset >= skillStart and note.time_offset <= skillEnd):
                self.skillProcs.append((skillProc, note.real_weight * mult))

                idx += 1
                continue
                
            elif note.time_offset > skillEnd:
                skillProc += 1
                skillStart += cooldown
                skillEnd += cooldown
            
            self.skillProcs.append((0, 0))
            
            idx += 1
        
        self.skillProcs = np.array(self.skillProcs)

        return self.skillProcs
    
    def applyToChartRandom(self, playableNotes, random_state=None):
        if random_state is not None:
            random.seed(random_state)
            
        probability = self.getProbability()
        skillProcs = self.getSkillProcs(playableNotes)
        
        if len(skillProcs) == 0:
            return np.zeros(0, dtype=bool)

        # Get the total number of skill activation windows (cast max to int)
        total_skills = int(np.max(skillProcs[:, 0]))
        
        if total_skills == 0:
            return np.zeros(len(playableNotes), dtype=bool)

        # Roll proc chance independently for each skill window (1 to total_skills)
        # procced_skill_ids will be a set of skill IDs (e.g. {1, 3}) that successfully activated
        procced_skill_ids = {
            s_id for s_id in range(1, total_skills + 1) 
            if random.random() < probability
        }
        
        # Generate a boolean array matching playableNotes length:
        # True if the note's skill ID is in our set of procced skills
        procd_mask = np.isin(skillProcs[:, 0], list(procced_skill_ids))
        
        return np.where(procd_mask, skillProcs[:, 1], 0)
    
    def applyToChartProbability(self, playableNotes):
        
        mult = self.getMult()
        cooldown = self.getCooldown()
        duration = self.getDuration()
        probability = self.getProbability()
        
        noteWeights = []
        
        idx = 0
        skillStart = cooldown
        skillEnd = cooldown + duration
        
        while idx < len(playableNotes):
            note = playableNotes[idx]
            
            if (note.time_offset >= skillStart and note.time_offset <= skillEnd):
                noteWeights.append([note.real_weight * mult, probability])

                idx += 1
                continue
                
            elif note.time_offset > skillEnd:
                skillStart += cooldown
                skillEnd += cooldown
            
            noteWeights.append(0)
            
            idx += 1

        return noteWeights
        
    def getCooldown(self):
        return float(self.cooldown / 1000.0)
    
    def getDuration(self):
        return float(self.duration / 1000.0)
    
    def getProbability(self):
        return float(self.activation_chance / 1000.0)
    
    def __str__(self):
        
        # mult = self.getMult()
        # cooldown = self.getCooldown()
        # duration = self.getDuration()
        # probability = self.getProbability()
        
        # return f'{mult:.2f}x for {duration:.2f}s with {probability:.2%} chance and {cooldown:.2f}s cooldown'
        
        return self.description