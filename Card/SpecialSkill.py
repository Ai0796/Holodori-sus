import re

import json
import numpy as np

from lib.master_data import MasterData
from lib.language import Lang

class SpecialSkill():
    
    def __init__(self, card):
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
        
        self.card = card
        self.master_data = card.master_data
        self.lang = card.lang
        
    def initByName(self, skill_id):
        skills = self.master_data.LiveSpecialSkillLevel
            
        for skill in skills:
            if skill['liveSpecialSkillId'] == skill_id and skill['level'] == 2:
                self.initByDict(skill)
                break
    
    def initByDict(self, skill_object: dict):
        self.skill_id = skill_object.get('liveSpecialSkillId', None)
        self.level = skill_object.get('level', None)
        self.skill_effect = skill_object.get('liveActiveSkillEffectGroupId', None)
        self.additional_skill = skill_object.get('additionalLiveActiveSkillEffectGroupId', None)

        self.descriptionId = skill_object.get('descriptionLangId', None)
        self.description = self.lang.LiveSpecialSkillLevel.get(self.descriptionId, None)
        
        self.duration = skill_object.get('effectDurationMillisecond', None)
    
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
        
        if 'score_up' not in skill_effect and 'score_up' in self.additional_skill:
            skill_effect = self.additional_skill_effect
        elif 'score_up' not in skill_effect and 'score_up' not in self.additional_skill:
            return 1.0
        
        mult = float(skill_effect.split('-')[-1]) / 1000.0
        
        return 1 + mult
    
    def getDuration(self):
        return self.duration / 1000.0
    
    def applyToChart(self, playableNotes, supportSkills):
        if self.noteWeights is not None and len(self.noteWeights) == len(playableNotes):
            return self.noteWeights
        
        mult = self.getMult()
        duration = self.getDuration()
        
        noteWeights = [(0, 1) for _ in range(len(playableNotes))]
        
        for i, start in enumerate(supportSkills, start=1):
            
            for j, note in enumerate(playableNotes):
                if note.time_offset >= start and note.time_offset < start + duration:
                    noteWeights[j] = (i, mult)
                    
        self.noteWeights = np.array(noteWeights)
        
        return self.noteWeights
    
    def __str__(self):
        
        mult = self.getMult()
        duration = self.getDuration()
        
        return f'{(mult - 1) * 100:.2f}% for {duration:.2f}s'
        
        return self.description