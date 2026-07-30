import re

import json
import numpy as np

from lib.master_data import MasterData
from lib.language import Lang

class SpecialSkill():
    
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
        
        self.master_data = master_data
        self.lang = lang
        
    def initByName(self, skill_id):
        skills = self.master_data.LiveSpecialSkillLevel
            
        for skill in skills:
            if skill['liveSpecialSkillId'] == skill_id and skill['level'] == 2:
                self.initByDict(skill)
                break
    
    def initByDict(self, skill_object: dict):
        self.skill_id = skill_object.get('liveSpecialSkillId', None)
        self.level = skill_object.get('level', None)
        self.skill_effect = skill_object.get('liveSpecialSkillEffectGroupId', None)
        self.additional_skill = skill_object.get('additionalLiveSpecialSkillEffectGroupId', None)

        self.descriptionId = skill_object.get('descriptionLangId', None)
        self.description = self.lang.LiveSpecialSkillLevel.get(self.descriptionId, None)
    
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
    
    def __str__(self):
        
        return self.description