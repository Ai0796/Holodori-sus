from Card.Skill import Skill

class Card():
    def __init__(self):
        self.card_name = None
        self.card_id = None
        self.card_rarity = None
        self.card_type = None
        self.active_skill = None
        
    def initByDict(self, card_object: dict):
        self.card_id = card_object.get('id', None)
        self.card_rarity = card_object.get('rarity', None)
        self.card_type = card_object.get('attributeType', None)
        
        if 'livePassiveSkillId' in card_object:
            self.active_skill = Skill()
            self.active_skill.initByName(card_object['liveActiveSkillId'])