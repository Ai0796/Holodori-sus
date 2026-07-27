            
from glob import glob
import os
import re
import json

class Lang():
    
    def __init__(self, language='Eng'):
        self.language = language
        self.langPath = f'master_data/json/Lang*{language}.json'
        
        self._files = {}
        
        for fp in glob(self.langPath):
            
            assetName = re.match(r'Lang(.+)_\w+\.json', os.path.basename(fp)).group(1)
            
            self._files[assetName] = str(fp)
    
    def __getattr__(self, name):
        if name in self._files:
            fp = self._files[name]
            
            addDict = {}
            
            
            with open(fp, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
                
            for value in data:
                if 'id' not in value: continue
                
                addDict[value['id']] = value.get('text', None)
                
            ## for effects such as skill effects, the descriptions are auto translated,
            ## As such we have to check if a fallback file exists
            fp = fp.name ## I have no clue why it becomes a io.TextIOWrapper object, but it does. So we have to get the name attribute to get the actual file path
            generated_fp = str(fp.replace(f'Lang{name}', f'LangGenerated{name}'))

            if os.path.exists(generated_fp):
                
                with open(generated_fp, 'r', encoding='utf-8') as fp:
                    data = json.load(fp)
                    
                for value in data:
                    if 'id' not in value: continue
                    
                    addDict[value['id']] = value.get('text', None)
            
            setattr(self, name, addDict)
            
            return getattr(self, name)
        
        raise AttributeError(f"'Lang' object has no attribute '{name}'")
    
if __name__ == "__main__":
    lang = Lang()
    print(lang.Card['la-card_name-00001-3-nrml-0000-00'])