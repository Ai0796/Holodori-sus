from Card.ActiveSkill import ActiveSkill
from Card.PassiveSkill import PassiveSkill
from Card.SpecialSkill import SpecialSkill
import json
from lib.master_data import MasterData
from lib.language import Lang

class Card():
    def __init__(self, master_data: MasterData, lang: Lang):
        self.card_name = None
        self.card_id = None
        self.card_rarity = None
        self.card_type = None
        self.active_skill = None
        self.passive_skill = None
        
        self.master_data = master_data
        self.lang = lang
        
    def initByDict(self, card_object: dict):
        self.card_id = card_object.get('id', None)
        self.card_rarity = card_object.get('rarity', None)
        self.card_type = card_object.get('attributeType', None)
        
        self.card_name = self.lang.Card.get(card_object['nameLangId'], None)
        
        self.character_name = self.master_data.getKeyById('Character', 'nameEng', card_object['characterId'])
        self.groups = self.master_data.getKeyById('Character', 'regularCharacterGroupingIds', card_object['characterId'])
        
        self.performance_mult = card_object.get('performancePermilMultiply', None)
        self.technique_mult = card_object.get('techniquePermilMultiply', None)
        self.sense_mult = card_object.get('sensePermilMultiply', None)
        
        if 'liveActiveSkillId' in card_object:
            self.active_skill = ActiveSkill(self.master_data, self.lang)
            self.active_skill.initByName(card_object['liveActiveSkillId'])
            
        if 'livePassiveSkillId' in card_object:
            self.passive_skill = PassiveSkill(self.master_data, self.lang)
            self.passive_skill.initByName(card_object['livePassiveSkillId'])
            
        if 'liveSpecialSkillId' in card_object:
            self.special_skill = SpecialSkill(self.master_data, self.lang)
            self.special_skill.initByName(card_object['liveSpecialSkillId'])
            
    def initById(self, card_id):
        cards = self.master_data.Card
            
        for card in cards:
            if card['id'] == card_id:
                self.initByDict(card)
                break
            
        
    def __str__(self):
        return f"Card({self.card_id}: {self.character_name} - {self.card_name}, {self.card_rarity}, {self.card_type}"