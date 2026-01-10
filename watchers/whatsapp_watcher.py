"""WhatsApp Watcher - Playwright automation"""
import os
import logging
from pathlib import Path
from datetime import datetime
try:
    from .base_watcher import BaseWatcher
except ImportError:
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
                browser = p.firefox.launch_persistent_context(
                    str(self.session_path), headless=True
                )
                page = browser.pages[0] if browser.pages else browser.new_page()

                try:
                    page.goto('https://web.whatsapp.com', timeout=60000)

                    # Wait for WhatsApp to load - try multiple selectors
                    try:
                        page.wait_for_selector('#pane-side', timeout=30000)
                    except:
                        page.wait_for_selector('[data-testid="chatlist"]', timeout=15000)

                    # Give it a moment to fully render
                    page.wait_for_timeout(5000)

                    # Get all chat rows from sidebar
                    chat_rows = page.query_selector_all('#pane-side > div > div > div > div')
                    logger.info(f"Found {len(chat_rows)} chat rows")

                    for row in chat_rows[:20]:  # Check first 20 chats
                        try:
                            text = row.inner_text()
                            text_lower = text.lower()

                            # Check for keyword match
                            if any(kw in text_lower for kw in self.keywords):
                                # Extract sender name (first line before |)
                                sender = text.split('\n')[0].strip() if '\n' in text else text.split('|')[0].strip()

                                # Click into chat to get full message
                                full_message = ""
                                try:
                                    row.click()
                                    page.wait_for_timeout(2000)

                                    # Get messages from conversation
                                    msg_elements = page.query_selector_all('[data-testid="msg-container"]')
                                    if msg_elements:
                                        # Get last few messages
                                        recent_msgs = msg_elements[-5:] if len(msg_elements) > 5 else msg_elements
                                        for msg_el in recent_msgs:
                                            try:
                                                msg_text = msg_el.inner_text()
                                                if msg_text and len(msg_text) > 5:
                                                    full_message += msg_text + "\n---\n"
                                            except:
                                                pass
                                except Exception as click_err:
                                    logger.debug(f"Could not click into chat: {click_err}")
                                    full_message = text[:200]

                                # Use full message if we got it, otherwise use preview
                                if not full_message:
                                    full_message = text[:200]

                                messages.append({
                                    'text': full_message[:500] if full_message else text[:200],
                                    'sender': sender,
                                    'full_text': full_message[:1000] if full_message else text[:200]
                                })
                                logger.info(f"Keyword match from {sender}")
                        except Exception as e:
                            continue

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
from: {item.get('sender', 'Unknown')}
received: {datetime.now().isoformat()}
priority: high
status: pending
---

## From
{item.get('sender', 'Unknown')}

## Message
{item.get('text', 'Message')}

## Full Context
{item.get('full_text', '')}

## Actions
- [ ] Reply
- [ ] Forward to email
- [ ] Mark as done
"""
            import hashlib
            unique_id = hashlib.md5(item.get('full_text', '')[:50].encode()).hexdigest()[:8]
            filepath = self.inbox / f"WHATSAPP_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{unique_id}.md"
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
