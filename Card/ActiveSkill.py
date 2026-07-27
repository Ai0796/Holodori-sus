import re

import json
import numpy as np

from lib.master_data import MasterData
from lib.language import Lang

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
        
        self.note_weights = None
        
        self.master_data = master_data
        self.lang = lang
        
    def initByName(self, skill_id):
        skills = self.master_data.LiveActiveSkillLevel
            
        for skill in skills:
            if skill['liveActiveSkillId'] == skill_id and skill['level'] == 1:
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
        
        if self.note_weights is not None:
            return self.note_weights
        
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
                skillStart += cooldown + duration
                skillEnd += cooldown + duration
            
            self.noteWeights.append(0)
            self.expectedWeights.append(0)
            idx += 1
        
        self.noteWeights = np.array(self.noteWeights)
        self.expectedWeights = np.array(self.expectedWeights)
        return self.noteWeights
        
    def getCooldown(self):
        return float(self.cooldown / 1000.0)
    
    def getDuration(self):
        return float(self.duration / 1000.0)
    
    def getProbability(self):
        return float(self.activation_chance / 1000.0)
    
    def __str__(self):
        
        mult = self.getMult()
        cooldown = self.getCooldown()
        duration = self.getDuration()
        probability = self.getProbability()
        
        return f'{mult:.2f}x for {duration:.2f}s with {probability:.2%} chance and {cooldown:.2f}s cooldown'