"""Social Post Drafter - OpenAI-powered multi-platform post generation"""
import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, Dict

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)

class SocialPostDrafter:
    """Uses OpenAI to generate posts for Twitter, Facebook, and LinkedIn"""

    def __init__(self, vault_path: str):
        self.vault = Path(vault_path)
        self.pending = self.vault / 'Pending_Approval'
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = "gpt-4o-mini"
        self.client = None

        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                logger.info("✓ SocialPostDrafter initialized (OpenAI gpt-4o-mini)")
            except ImportError:
                logger.error("OpenAI SDK not installed")
        else:
            logger.warning("OPENAI_API_KEY not set - post drafting unavailable")

    def draft_posts(self, topic: str, context: str = "", style: str = "professional") -> Dict[str, Path]:
        """Generate posts for Twitter, Facebook, and LinkedIn. Returns dict of platform: draft_path"""

        if not self.client:
            logger.warning("OpenAI not configured - skipping post drafting")
            return {}

        results = {}

        # Generate Twitter post (280 chars)
        twitter_text, twitter_conf = self._generate_twitter_post(topic, context, style)
        if twitter_text:
            twitter_path = self._create_draft_file("twitter", topic, twitter_text, twitter_conf, context)
            if twitter_path:
                results['twitter'] = twitter_path
                logger.info(f"✓ Twitter draft created: {twitter_path.name}")

        # Generate Facebook post (longer, conversational)
        facebook_text, facebook_conf = self._generate_facebook_post(topic, context, style)
        if facebook_text:
            facebook_path = self._create_draft_file("facebook", topic, facebook_text, facebook_conf, context)
            if facebook_path:
                results['facebook'] = facebook_path
                logger.info(f"✓ Facebook draft created: {facebook_path.name}")

        # Generate LinkedIn post (professional, detailed)
        linkedin_text, linkedin_conf = self._generate_linkedin_post(topic, context, style)
        if linkedin_text:
            linkedin_path = self._create_draft_file("linkedin", topic, linkedin_text, linkedin_conf, context)
            if linkedin_path:
                results['linkedin'] = linkedin_path
                logger.info(f"✓ LinkedIn draft created: {linkedin_path.name}")

        return results

    def _generate_twitter_post(self, topic: str, context: str, style: str) -> Tuple[str, float]:
        """Generate Twitter post (max 280 chars)"""
        prompt = f"""Generate a {style} tweet about: {topic}

Context: {context if context else 'N/A'}

REQUIREMENTS:
1. Maximum 280 characters (strict)
2. Engaging and shareable
3. Include 2-3 relevant hashtags
4. Professional tone
5. Call to action if possible

Return ONLY the tweet text, nothing else."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a social media expert creating concise, professional tweets."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=100
            )
            tweet = response.choices[0].message.content.strip()
            if len(tweet) > 280:
                tweet = tweet[:277] + "..."
            return tweet, 0.90
        except Exception as e:
            logger.error(f"Twitter draft error: {e}")
            return "", 0.0

    def _generate_facebook_post(self, topic: str, context: str, style: str) -> Tuple[str, float]:
        """Generate Facebook post (conversational, longer)"""
        prompt = f"""Generate a {style} Facebook post about: {topic}

Context: {context if context else 'N/A'}

REQUIREMENTS:
1. Conversational but professional tone
2. 2-4 paragraphs (150-300 words)
3. Emoji OK (1-2 max)
4. End with engagement question
5. No hashtags (Facebook doesn't need them)

Return ONLY the post text, nothing else."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a social media expert creating engaging, friendly Facebook posts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=300
            )
            return response.choices[0].message.content.strip(), 0.90
        except Exception as e:
            logger.error(f"Facebook draft error: {e}")
            return "", 0.0

    def _generate_linkedin_post(self, topic: str, context: str, style: str) -> Tuple[str, float]:
        """Generate LinkedIn post (professional, thought leadership)"""
        prompt = f"""Generate a professional LinkedIn post about: {topic}

Context: {context if context else 'N/A'}

REQUIREMENTS:
1. Professional and insightful
2. Thought leadership tone
3. 2-4 paragraphs (200-400 words)
4. Include key takeaway at the end
5. Relevant hashtags (#AI #Automation #Leadership etc)
6. Call to action (discussion, feedback, connection)

Return ONLY the post text, nothing else."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a thought leader creating professional LinkedIn posts about AI, automation, and business."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=400
            )
            return response.choices[0].message.content.strip(), 0.90
        except Exception as e:
            logger.error(f"LinkedIn draft error: {e}")
            return "", 0.0

    def _create_draft_file(self, platform: str, topic: str, content: str, confidence: float, context: str) -> Optional[Path]:
        """Create draft file in Pending_Approval"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        platform_upper = platform.upper()
        draft_filename = f"{platform_upper}_DRAFT_{timestamp}.md"
        draft_path = self.pending / draft_filename

        draft_markdown = f"""---
type: social_post
platform: {platform}
topic: {topic}
created: {datetime.now().isoformat()}
confidence: {confidence:.2f}
ai_generated: true
status: pending_approval
---

## Original Request

**Topic**: {topic}
**Platform**: {platform.title()}

**Context**: {context if context else 'None provided'}

---

## AI Analysis

**Confidence**: {confidence*100:.0f}%
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Proposed Post

{content}

---

## Actions

- [ ] Approve and move to /Approved/ to post
- [ ] Edit content above
- [ ] Reject (delete file)

**Instructions**:
1. Review the generated post
2. Edit if needed
3. Move to /Approved/ folder to auto-post
4. Result will be logged to /vault/Logs/

---

*Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

        try:
            self.pending.mkdir(parents=True, exist_ok=True)
            draft_path.write_text(draft_markdown)
            return draft_path
        except Exception as e:
            logger.error(f"Failed to create draft file: {e}")
            return None
