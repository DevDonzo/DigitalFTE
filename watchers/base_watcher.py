"""Base Watcher Abstract Class - All watchers inherit from this"""
import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime
import json

class BaseWatcher(ABC):
    def __init__(self, vault_path: str, check_interval: int = 60):
        self.vault_path = Path(vault_path)
        self.inbox = self.vault_path / 'Inbox'
        self.needs_action = self.vault_path / 'Needs_Action'
        self.check_interval = check_interval
        self.logger = logging.getLogger(self.__class__.__name__)
        self.processed_ids = set()
        
    @abstractmethod
    def check_for_updates(self) -> list:
        """Return list of new items to process"""
        pass
      
    @abstractmethod
    def create_action_file(self, item) -> Path:
        """Create .md file in Inbox folder"""
        pass
      
    def run(self):
        self.logger.info(f'Starting {self.__class__.__name__}')
        while True:
            try:
                items = self.check_for_updates()
                for item in items:
                    self.create_action_file(item)
                    self.log_action('watcher_detected_event', 
                                  action_type=self.__class__.__name__,
                                  result='success')
            except Exception as e:
                self.logger.error(f'Error: {e}')
                self.log_action('watcher_error',
                              action_type=self.__class__.__name__,
                              result='failure',
                              error=str(e))
            time.sleep(self.check_interval)
    
    def log_action(self, event_type: str, action_type: str = None, result: str = 'pending', **kwargs):
        """Log action to audit trail"""
        log_file = self.vault_path / 'Logs' / f'{datetime.now().strftime("%Y-%m-%d")}.json'
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'event_type': event_type,
            'action_type': action_type or self.__class__.__name__,
            'actor': 'watcher',
            'result': result,
            **kwargs
        }
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
