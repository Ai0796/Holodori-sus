from lib.master_data import MasterData
from lib.language import Lang

class PassiveSkill():
    
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
        
        self.note_weights = None
        
        self.card = card
        self.master_data = card.master_data
        self.lang = card.lang
        
    def initByName(self, skill_id):
        skills = self.master_data.LivePassiveSkillLevel
            
        for skill in skills:
            if skill['livePassiveSkillId'] == skill_id and skill['level'] == 2:                
                self.initByDict(skill)
                break
    
    def initByDict(self, skill_object: dict):
        self.skill_id = skill_object.get('livePassiveSkillId', None)
        self.level = skill_object.get('level', None)
        self.skill_effect_id = skill_object.get('livePassiveSkillEffectGroupId', None)
        self.descriptionAsset = skill_object.get('descriptionLangId', None)
        self.description = self.lang.LivePassiveSkillLevel.get(self.descriptionAsset, None)
        
        ## might not have one
        self.skill_trigger = skill_object.get('liveSkillTriggerGroupId', None)
        
        self.skill_effect = self.master_data.getEntity('LivePassiveSkillEffect', self.skill_effect_id, 'groupId')
        
        self.skill_effect_number = self.skill_effect.get('number', None)
        self.skill_effect_type = self.skill_effect.get('type', None)
        self.skill_effect_value = self.skill_effect.get('value', None)
        self.skill_effect_target_id = self.skill_effect.get('liveSkillEffectTargetId', None)
        self.skill_effect_description_id = self.skill_effect.get('descriptionLangId', None)
        
        self.skill_effect_description = self.lang.LivePassiveSkillEffect.get(self.skill_effect_description_id, None)
    
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
        
        return f"Passive Skill: {self.description} ({self.skill_effect_description} - {self.skill_effect_value})"
    
class AttributePassive():
    def __init__(self, skillString, master_data: MasterData, lang: Lang):
        ## Example: live_skill_effect_target-attribute-attribute_2-2
        skillParts = skillString.split('_')[3:]