"""WhatsApp Watcher - Playwright automation"""
import os
import logging
from pathlib import Path
from datetime import datetime
from base_watcher import BaseWatcher

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("ERROR: pip install playwright")
    print("Then: playwright install chromium")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhatsAppWatcher(BaseWatcher):
    def __init__(self, vault_path: str, session_path: str = None):
        super().__init__(vault_path, check_interval=30)
        self.session_path = Path(session_path or Path.home() / '.whatsapp_session')
        self.keywords = os.getenv('WHATSAPP_KEYWORDS', 'urgent,asap,invoice,payment,help').split(',')
        
    def check_for_updates(self) -> list:
        """Check WhatsApp Web for keyword-matching messages"""
        messages = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    str(self.session_path), headless=True
                )
                page = browser.pages[0] if browser.pages else browser.new_page()
                
                try:
                    page.goto('https://web.whatsapp.com', timeout=30000)
                    page.wait_for_selector('[data-testid="chat"]', timeout=10000)
                    
                    # Get unread chats
                    chats = page.query_selector_all('[aria-label*="unread"]')
                    for chat in chats[:5]:  # Limit to 5
                        text = chat.inner_text().lower()
                        if any(kw in text for kw in self.keywords):
                            messages.append({'text': text, 'chat': chat})
                except Exception as e:
                    logger.warning(f"WhatsApp page error: {e}")
                
                browser.close()
        except Exception as e:
            logger.error(f"WhatsApp watcher error: {e}")
        
        return messages
      
    def create_action_file(self, item) -> Path:
        """Create markdown file for WhatsApp message"""
        try:
            content = f"""---
type: whatsapp
from: {item.get('text', '').split(':')[0]}
received: {datetime.now().isoformat()}
priority: high
status: pending
---

## Message
{item.get('text', 'Message')}

## Actions
- [ ] Reply
- [ ] Forward to email
- [ ] Mark as done
"""
            filepath = self.inbox / f"WHATSAPP_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            filepath.write_text(content)
            logger.info(f"Created: {filepath.name}")
            return filepath
        except Exception as e:
            logger.error(f"File creation error: {e}")
            return None

if __name__ == '__main__':
    vault_path = os.getenv('VAULT_PATH', './vault')
    session_path = os.getenv('WHATSAPP_SESSION_PATH')
    watcher = WhatsAppWatcher(vault_path, session_path)
    watcher.run()
