from lib.master_data import MasterData
from lib.language import Lang

class PassiveSkill():
    
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
        skills = self.master_data.LivePassiveSkillLevel
        
        print(f"Searching for passive skill {skill_id} in master data...")
            
        for skill in skills:
            if skill['livePassiveSkillId'] == skill_id and skill['level'] == 1:                
                self.initByDict(skill)
                break
    
    def initByDict(self, skill_object: dict):
        self.skill_id = skill_object.get('livePassiveSkillId', None)
        self.level = skill_object.get('level', None)
        self.skill_effect_id = skill_object.get('livePassiveSkillEffectGroupId', None)
        self.descriptionAsset = skill_object.get('descriptionLangId', None)
        print(f"Loading passive skill description for {self.skill_id} from {self.descriptionAsset}")
        self.description = self.lang.LivePassiveSkillLevel.get(self.descriptionAsset, None)
        
        self.skill_effect = self.master_data.getEntity('LivePassiveSkillEffect', self.skill_effect_id, 'groupId')
        
        print(self.skill_effect)
        
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