import json
from glob import glob
import os
import re

masterPath = 'master_data/json/'

class MasterData():
    
    def __init__(self):
        
        self._files = {}
        
        for fp in glob(masterPath + '*.json'):
            key = os.path.splitext(os.path.basename(fp))[0]
            
            ## Don't store language specific files
            if key.startswith('Lang'):
                continue
            
            self._files[key] = fp
            # setattr(self, os.path.splitext(os.path.basename(fp))[0], json.load(open(fp, 'r', encoding='utf-8')))
            
    def getKeyById(self, asset, key, id, lookup='id'):
        if not hasattr(self, asset):
            raise AttributeError(f"'MasterData' object has no attribute '{asset}'")
        
        asset_data = getattr(self, asset)
        
        for item in asset_data:
            if item.get(lookup) == id:
                return item.get(key)
        
        return None
    
    def getEntity(self, asset, id, lookup='id'):
        if not hasattr(self, asset):
            raise AttributeError(f"'MasterData' object has no attribute '{asset}'")
        
        asset_data = getattr(self, asset)
        
        for item in asset_data:
            if item.get(lookup) == id:
                return item
        
        return None
            
    def __getattr__(self, name):
        if name in self._files:
            fp = self._files[name]
            
            with open(fp, 'r', encoding='utf-8') as f:
                return json.load(f)
            
            setattr(self, name, json.load(open(fp, 'r', encoding='utf-8')))
            
            return getattr(self, name)
        
        raise AttributeError(f"'MasterData' object has no attribute '{name}'")


if __name__ == "__main__":
    masterData = MasterData()
    print(masterData.Card[0])