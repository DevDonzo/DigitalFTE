"""LinkedIn Watcher - Monitor LinkedIn and post content via Official API"""
import os
import json
import logging
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from .base_watcher import BaseWatcher
except ImportError:
    from base_watcher import BaseWatcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LinkedInAPI:
    """LinkedIn Official API client for posting and reading"""

    BASE_URL = "https://api.linkedin.com/v2"

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        self.user_id = None

    def get_profile(self) -> Optional[Dict]:
        """Get authenticated user's profile"""
        try:
            response = requests.get(
                f"{self.BASE_URL}/userinfo",
                headers=self.headers
            )
            if response.status_code == 200:
                data = response.json()
                self.user_id = data.get("sub")
                return data
            else:
                # Try legacy endpoint
                response = requests.get(
                    f"{self.BASE_URL}/me",
                    headers=self.headers
                )
                if response.status_code == 200:
                    data = response.json()
                    self.user_id = data.get("id")
                    return data
                logger.error(f"Profile fetch failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Profile error: {e}")
            return None

    def post_text(self, text: str) -> Optional[Dict]:
        """Post text content to LinkedIn feed"""
        if not self.user_id:
            self.get_profile()

        if not self.user_id:
            logger.error("Cannot post: user ID not available")
            return None

        payload = {
            "author": f"urn:li:person:{self.user_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        try:
            response = requests.post(
                f"{self.BASE_URL}/ugcPosts",
                headers=self.headers,
                json=payload
            )

            if response.status_code in [200, 201]:
                logger.info(f"Posted to LinkedIn successfully")
                return response.json()
            else:
                logger.error(f"Post failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Post error: {e}")
            return None

    def post_with_link(self, text: str, url: str, title: str = "", description: str = "") -> Optional[Dict]:
        """Post content with a link to LinkedIn feed"""
        if not self.user_id:
            self.get_profile()

        if not self.user_id:
            logger.error("Cannot post: user ID not available")
            return None

        payload = {
            "author": f"urn:li:person:{self.user_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "ARTICLE",
                    "media": [{
                        "status": "READY",
                        "originalUrl": url,
                        "title": {"text": title} if title else None,
                        "description": {"text": description} if description else None
                    }]
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        # Clean up None values
        media = payload["specificContent"]["com.linkedin.ugc.ShareContent"]["media"][0]
        if media.get("title") is None:
            del media["title"]
        if media.get("description") is None:
            del media["description"]

        try:
            response = requests.post(
                f"{self.BASE_URL}/ugcPosts",
                headers=self.headers,
                json=payload
            )

            if response.status_code in [200, 201]:
                logger.info(f"Posted to LinkedIn with link successfully")
                return response.json()
            else:
                logger.error(f"Post failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Post error: {e}")
            return None

    def get_shares(self, count: int = 10) -> List[Dict]:
        """Get recent shares/posts (requires r_organization_social or similar scope)"""
        try:
            response = requests.get(
                f"{self.BASE_URL}/shares?q=owners&owners=urn:li:person:{self.user_id}&count={count}",
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json().get("elements", [])
            else:
                logger.warning(f"Could not fetch shares: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Shares fetch error: {e}")
            return []


class LinkedInWatcher(BaseWatcher):
    """LinkedIn Watcher for monitoring and posting"""

    def __init__(self, vault_path: str, access_token: str = None):
        super().__init__(vault_path, check_interval=300)  # Check every 5 minutes
        self.access_token = access_token or os.getenv('LINKEDIN_ACCESS_TOKEN')
        self.api = LinkedInAPI(self.access_token) if self.access_token else None
        self.processed_file = Path(vault_path) / '.processed_linkedin'
        self.processed_ids = self._load_processed()

        if self.api:
            profile = self.api.get_profile()
            if profile:
                logger.info(f"LinkedIn connected: {profile.get('name', profile.get('localizedFirstName', 'User'))}")
            else:
                logger.warning("LinkedIn token may be invalid or expired")

    def _load_processed(self) -> set:
        """Load previously processed item IDs"""
        if self.processed_file.exists():
            return set(self.processed_file.read_text().strip().split('\n'))
        return set()

    def _save_processed(self, item_id: str):
        """Save processed item ID"""
        self.processed_ids.add(item_id)
        with open(self.processed_file, 'a') as f:
            f.write(f"{item_id}\n")

    def check_for_updates(self) -> list:
        """Check LinkedIn for updates (limited by API restrictions)"""
        if not self.api:
            logger.warning("LinkedIn access token not configured")
            return []

        updates = []

        # LinkedIn API is very restricted for reading
        # Main use case is posting content from the vault
        # Check for pending LinkedIn posts in vault
        try:
            pending_posts = list((Path(self.vault_path) / 'Approved').glob('LINKEDIN_POST_*.md'))
            for post_file in pending_posts:
                if post_file.name not in self.processed_ids:
                    updates.append({
                        'type': 'pending_post',
                        'file': post_file,
                        'id': post_file.name
                    })
        except Exception as e:
            logger.error(f"Error checking pending posts: {e}")

        return updates

    def create_action_file(self, item) -> Path:
        """Create action file for LinkedIn activity"""
        try:
            if item.get('type') == 'pending_post':
                # This is an approved post - execute it
                return self._execute_post(item['file'])

            message_type = item.get('type', 'notification')
            sender = item.get('from', 'LinkedIn')

            content = f"""---
type: linkedin
message_type: {message_type}
from: {sender}
received: {datetime.now().isoformat()}
priority: medium
status: pending
---

## From
{sender}

## Message Type
{message_type}

## Content
{item.get('content', 'LinkedIn notification')}

## Actions
- [ ] Reply
- [ ] View on LinkedIn
- [ ] Mark as done
"""
            filepath = self.inbox / f"LINKEDIN_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            filepath.write_text(content)
            self._save_processed(item.get('id', filepath.name))
            logger.info(f"Created: {filepath.name}")
            return filepath
        except Exception as e:
            logger.error(f"File creation error: {e}")
            return None

    def _execute_post(self, post_file: Path) -> Optional[Path]:
        """Execute a LinkedIn post from approved file"""
        try:
            content = post_file.read_text()

            # Extract post content from markdown
            lines = content.split('\n')
            post_text = ""
            post_url = None
            in_content = False

            for line in lines:
                if line.startswith('## Content') or line.startswith('## Post'):
                    in_content = True
                    continue
                elif line.startswith('## ') and in_content:
                    break
                elif in_content and line.strip():
                    if line.startswith('url:'):
                        post_url = line.replace('url:', '').strip()
                    else:
                        post_text += line + "\n"

            post_text = post_text.strip()

            if not post_text:
                logger.error(f"No content found in {post_file.name}")
                return None

            # Post to LinkedIn
            if post_url:
                result = self.api.post_with_link(post_text, post_url)
            else:
                result = self.api.post_text(post_text)

            if result:
                # Move to Done
                done_path = Path(self.vault_path) / 'Done' / post_file.name
                post_file.rename(done_path)
                self._save_processed(post_file.name)
                logger.info(f"LinkedIn post published: {post_file.name}")

                # Log the post
                self._log_post(post_text, result)
                return done_path
            else:
                logger.error(f"Failed to post: {post_file.name}")
                return None

        except Exception as e:
            logger.error(f"Post execution error: {e}")
            return None

    def _log_post(self, text: str, result: dict):
        """Log successful post"""
        log_file = Path(self.vault_path) / 'Logs' / 'linkedin_posts.jsonl'
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "text": text[:200],
            "post_id": result.get("id", "unknown"),
            "status": "published"
        }
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

    def post_now(self, text: str, url: str = None) -> bool:
        """Immediately post to LinkedIn"""
        if not self.api:
            logger.error("LinkedIn API not configured")
            return False

        if url:
            result = self.api.post_with_link(text, url)
        else:
            result = self.api.post_text(text)

        if result:
            self._log_post(text, result)
            return True
        return False


def test_linkedin():
    """Test LinkedIn API connection"""
    token = os.getenv('LINKEDIN_ACCESS_TOKEN')
    if not token:
        print("LINKEDIN_ACCESS_TOKEN not set in .env")
        return False

    api = LinkedInAPI(token)
    profile = api.get_profile()

    if profile:
        print(f"Connected to LinkedIn!")
        print(f"  User ID: {api.user_id}")
        print(f"  Name: {profile.get('name', profile.get('localizedFirstName', 'N/A'))}")
        return True
    else:
        print("Failed to connect to LinkedIn - check your access token")
        return False


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        test_linkedin()
    else:
        vault_path = os.getenv('VAULT_PATH', './vault')
        token = os.getenv('LINKEDIN_ACCESS_TOKEN')
        watcher = LinkedInWatcher(vault_path, token)
        watcher.run()
