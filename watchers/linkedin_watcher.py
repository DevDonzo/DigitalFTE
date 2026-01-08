"""${watcher^^} Watcher"""
from base_watcher import BaseWatcher

class ${watcher^^}Watcher(BaseWatcher):
    def __init__(self, vault_path: str):
        super().__init__(vault_path)
        
    def check_for_updates(self) -> list:
        return []
      
    def create_action_file(self, item):
        pass

if __name__ == '__main__':
    import os
    watcher = ${watcher^^}Watcher(os.getenv('VAULT_PATH'))
    watcher.run()
