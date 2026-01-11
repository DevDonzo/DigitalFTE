"""Social Media Scheduler - Auto-post to LinkedIn & Facebook"""
import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import watchers for posting
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from watchers.linkedin_watcher import LinkedInAPI
    HAS_LINKEDIN = True
except ImportError:
    HAS_LINKEDIN = False
    LinkedInAPI = None

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SocialScheduler:
    """Manages scheduled social media posts for LinkedIn and Facebook"""

    def __init__(self, vault_path: str):
        self.vault = Path(vault_path)
        self.queue_dir = self.vault / 'Social_Queue'
        self.queue_dir.mkdir(parents=True, exist_ok=True)

        # Initialize APIs
        self.linkedin = None
        self.facebook_token = os.getenv('META_ACCESS_TOKEN')
        self.facebook_page_id = os.getenv('FACEBOOK_PAGE_ID')

        linkedin_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
        if linkedin_token and HAS_LINKEDIN:
            self.linkedin = LinkedInAPI(linkedin_token)
            logger.info("✅ LinkedIn API initialized")

        if self.facebook_token and self.facebook_page_id:
            logger.info("✅ Facebook API initialized")

        # OpenAI for content generation
        self.openai = None
        if HAS_OPENAI and os.getenv('OPENAI_API_KEY'):
            self.openai = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            logger.info("✅ OpenAI initialized for content generation")

    def create_post_file(self, content: str, platforms: list = None,
                         schedule_time: str = None) -> Path:
        """Create a post file in the queue"""
        if platforms is None:
            platforms = ['linkedin', 'facebook']

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"POST_{timestamp}.md"
        filepath = self.queue_dir / filename

        post_content = f"""---
type: social_post
platforms: {', '.join(platforms)}
scheduled: {schedule_time or 'immediate'}
status: pending
created: {datetime.now().isoformat()}
---

## Content

{content}

## Platforms
{chr(10).join([f'- [ ] {p.title()}' for p in platforms])}

## Instructions
Move to /Approved to post immediately, or edit schedule time above.
"""
        filepath.write_text(post_content)
        logger.info(f"📝 Post queued: {filename}")
        return filepath

    def generate_post(self, topic: str, style: str = "professional") -> str:
        """Use AI to generate a social media post"""
        if not self.openai:
            logger.warning("OpenAI not available for content generation")
            return f"[Draft post about: {topic}]"

        prompt = f"""Generate a LinkedIn/professional social media post about: {topic}

Style: {style}
Author: Hamza Paracha, 2nd year Computer Science student at University of Guelph
Focus: AI automation, Digital FTE development, Claude Code, Python

Requirements:
- 150-250 words
- Professional but approachable tone
- Include 2-3 relevant hashtags at the end
- No emojis unless specifically requested
- Focus on value and insights, not self-promotion

Write ONLY the post content, nothing else."""

        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            return f"[Draft post about: {topic}]"

    def post_to_linkedin(self, content: str, url: str = None) -> Optional[dict]:
        """Post content to LinkedIn"""
        if not self.linkedin:
            logger.error("LinkedIn API not configured")
            return None

        try:
            if url:
                result = self.linkedin.post_with_link(content, url)
            else:
                result = self.linkedin.post_text(content)

            if result:
                self._log_post('linkedin', content, result)
                logger.info("✅ Posted to LinkedIn")
            return result
        except Exception as e:
            logger.error(f"LinkedIn post failed: {e}")
            return None

    def post_to_facebook(self, content: str, url: str = None) -> Optional[dict]:
        """Post content to Facebook Page"""
        if not self.facebook_token or not self.facebook_page_id:
            logger.error("Facebook API not configured")
            return None

        import requests

        api_url = f"https://graph.facebook.com/v18.0/{self.facebook_page_id}/feed"

        payload = {
            'message': content,
            'access_token': self.facebook_token
        }

        if url:
            payload['link'] = url

        try:
            response = requests.post(api_url, data=payload)
            response.raise_for_status()
            result = response.json()
            self._log_post('facebook', content, result)
            logger.info("✅ Posted to Facebook")
            return result
        except Exception as e:
            logger.error(f"Facebook post failed: {e}")
            return None

    def post_to_all(self, content: str, url: str = None) -> dict:
        """Post to all configured platforms"""
        results = {}

        if self.linkedin:
            results['linkedin'] = self.post_to_linkedin(content, url)

        if self.facebook_token:
            results['facebook'] = self.post_to_facebook(content, url)

        return results

    def process_queue(self):
        """Process all pending posts in queue"""
        pending = list(self.queue_dir.glob('POST_*.md'))

        for post_file in pending:
            content = post_file.read_text()

            # Check if still pending
            if 'status: pending' not in content:
                continue

            # Extract post content
            lines = content.split('\n')
            post_text = ''
            in_content = False

            for line in lines:
                if line.strip() == '## Content':
                    in_content = True
                    continue
                elif line.startswith('## ') and in_content:
                    break
                elif in_content:
                    post_text += line + '\n'

            post_text = post_text.strip()

            if not post_text or post_text.startswith('[Draft'):
                continue

            # Extract platforms
            platforms = []
            if 'linkedin' in content.lower():
                platforms.append('linkedin')
            if 'facebook' in content.lower():
                platforms.append('facebook')

            # Post to platforms
            logger.info(f"📤 Processing: {post_file.name}")

            for platform in platforms:
                if platform == 'linkedin':
                    self.post_to_linkedin(post_text)
                elif platform == 'facebook':
                    self.post_to_facebook(post_text)

            # Move to done
            done_dir = self.vault / 'Done'
            done_dir.mkdir(exist_ok=True)
            post_file.rename(done_dir / post_file.name)
            logger.info(f"✅ Post completed: {post_file.name}")

    def _log_post(self, platform: str, content: str, result: dict):
        """Log posted content"""
        log_file = self.vault / 'Logs' / f'{platform}_posts.jsonl'
        log_file.parent.mkdir(parents=True, exist_ok=True)

        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'platform': platform,
            'content': content[:200],
            'result': str(result)[:100] if result else None,
            'status': 'posted'
        }

        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

    def generate_weekly_content(self) -> list:
        """Generate a week's worth of content based on Business_Goals.md"""
        goals_file = self.vault / 'Business_Goals.md'

        topics = [
            "Building autonomous AI agents with Claude Code",
            "How Digital FTEs can automate your email workflow",
            "My journey as a CS student building AI automation tools",
        ]

        # Check content queue in Business_Goals.md
        if goals_file.exists():
            content = goals_file.read_text()
            if '## Content Ideas Queue' in content:
                # Extract unchecked items
                for line in content.split('\n'):
                    if line.strip().startswith('- [ ]'):
                        topic = line.replace('- [ ]', '').strip().strip('"')
                        if topic and topic not in topics:
                            topics.append(topic)

        posts = []
        for topic in topics[:3]:  # Generate 3 posts
            post_content = self.generate_post(topic)
            post_file = self.create_post_file(post_content)
            posts.append(post_file)
            logger.info(f"📝 Generated post for: {topic[:50]}...")

        return posts


def quick_post(content: str, platforms: list = None):
    """Quick function to post immediately"""
    vault = os.getenv('VAULT_PATH', './vault')
    scheduler = SocialScheduler(vault)

    if platforms is None:
        platforms = ['linkedin', 'facebook']

    results = {}
    if 'linkedin' in platforms:
        results['linkedin'] = scheduler.post_to_linkedin(content)
    if 'facebook' in platforms:
        results['facebook'] = scheduler.post_to_facebook(content)

    return results


if __name__ == '__main__':
    import sys

    vault = os.getenv('VAULT_PATH', './vault')
    scheduler = SocialScheduler(vault)

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'generate':
            # Generate a week of content
            posts = scheduler.generate_weekly_content()
            print(f"Generated {len(posts)} posts in Social_Queue/")

        elif command == 'process':
            # Process pending queue
            scheduler.process_queue()

        elif command == 'post':
            # Quick post from command line
            if len(sys.argv) > 2:
                content = ' '.join(sys.argv[2:])
                results = scheduler.post_to_all(content)
                print(f"Posted: {results}")
            else:
                print("Usage: python social_scheduler.py post <content>")

        elif command == 'topic':
            # Generate post for specific topic
            if len(sys.argv) > 2:
                topic = ' '.join(sys.argv[2:])
                content = scheduler.generate_post(topic)
                print(f"\n{content}\n")

                confirm = input("Post this? (y/n): ")
                if confirm.lower() == 'y':
                    scheduler.post_to_all(content)
            else:
                print("Usage: python social_scheduler.py topic <topic>")

        else:
            print("Commands: generate, process, post <content>, topic <topic>")
    else:
        print("Social Media Scheduler")
        print("Commands:")
        print("  generate  - Generate a week of content")
        print("  process   - Post all pending items in queue")
        print("  post <x>  - Post content immediately")
        print("  topic <x> - Generate and optionally post about topic")
