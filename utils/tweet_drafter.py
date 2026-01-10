"""Tweet Drafter - OpenAI-powered autonomous tweet generation"""
import os
import json
import logging
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)

class TweetDrafter:
    """Uses OpenAI API to intelligently draft tweets"""

    def __init__(self, vault_path: str):
        self.vault = Path(vault_path)
        self.needs_action = self.vault / 'Needs_Action'
        self.pending = self.vault / 'Pending_Approval'
        self.processed_file = self.vault / '.processed_tweets'
        self.processed_ids = self._load_processed()
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = "gpt-3.5-turbo"
        self.client = None

        # Initialize OpenAI client
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                logger.info("✓ TweetDrafter initialized (OpenAI gpt-3.5-turbo)")
            except ImportError:
                logger.error("OpenAI SDK not installed. Install: pip install openai")
        else:
            logger.warning("OPENAI_API_KEY not set - tweet drafting unavailable")

    def _load_processed(self) -> set:
        """Load set of already-processed tweet request filenames"""
        if self.processed_file.exists():
            return set(self.processed_file.read_text().strip().split('\n'))
        return set()

    def _mark_processed(self, filename: str):
        """Track that this request has been processed"""
        self.processed_ids.add(filename)
        with open(self.processed_file, 'a') as f:
            f.write(filename + '\n')

    def _parse_request(self, request_file: Path) -> dict:
        """Parse tweet request markdown file"""
        content = request_file.read_text()

        # Parse frontmatter
        parts = content.split('---')
        metadata = {}

        if len(parts) >= 2:
            frontmatter = parts[1]
            for line in frontmatter.split('\n'):
                if ':' in line:
                    key, val = line.split(':', 1)
                    metadata[key.strip()] = val.strip()

        # Extract body/topic
        body = ''.join(parts[2:]) if len(parts) > 2 else ''

        return {
            'filename': request_file.name,
            'topic': metadata.get('topic', ''),
            'style': metadata.get('style', 'professional'),
            'hashtags': metadata.get('hashtags', ''),
            'context': body.strip(),
            'platform': metadata.get('platform', 'twitter')
        }

    def _generate_tweet(self, request: dict) -> Tuple[str, float]:
        """Use OpenAI to generate tweet content"""

        if not self.client:
            logger.warning("OpenAI not configured - using template")
            return self._generate_template(request), 0.7

        prompt = f"""Generate a professional tweet based on the following:

TOPIC: {request.get('topic', 'general update')}
STYLE: {request.get('style', 'professional')}
CONTEXT: {request.get('context', '')}
SUGGESTED HASHTAGS: {request.get('hashtags', '')}

REQUIREMENTS:
1. Maximum 280 characters (strict limit)
2. Professional but engaging tone
3. Include 2-3 relevant hashtags if space allows
4. Make it shareable and valuable
5. No emojis unless specifically requested

Return ONLY the tweet text, nothing else. No quotes around it."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": """You are a social media expert creating tweets for Hamza Paracha's AI Employee system.

Your tweets should be:
- Professional and business-focused
- Concise and impactful (max 280 chars)
- Include relevant hashtags
- Provide value to the audience
- Reflect expertise in AI, automation, and business

Topics often include: AI automation, productivity, business insights, tech trends."""},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=100
            )
            tweet = response.choices[0].message.content.strip()

            # Ensure 280 char limit
            if len(tweet) > 280:
                tweet = tweet[:277] + "..."

            logger.info(f"✓ Tweet generated via OpenAI ({len(tweet)} chars)")
            return tweet, 0.90

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return self._generate_template(request), 0.7

    def _generate_template(self, request: dict) -> str:
        """Fallback template if OpenAI unavailable"""
        topic = request.get('topic', 'productivity')
        return f"Exploring new ways to improve {topic}. The future of work is autonomous. #AI #Automation #DigitalFTE"

    def _create_draft_file(self, request: dict, tweet_text: str, confidence: float) -> Path:
        """Create POST draft file in Pending_Approval"""

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        draft_filename = f"POST_TWEET_{timestamp}.md"
        draft_path = self.pending / draft_filename

        draft_content = f"""---
type: social_post
platform: {request.get('platform', 'twitter')}
topic: {request.get('topic', 'general')}
created: {datetime.now().isoformat()}
confidence: {confidence:.2f}
ai_generated: true
status: pending_approval
---

## Original Request

**Topic**: {request.get('topic', 'Not specified')}
**Style**: {request.get('style', 'professional')}
**Context**: {request.get('context', 'None')}

---

## AI Analysis

**Confidence**: {confidence*100:.0f}%
**Character Count**: {len(tweet_text)}/280
**Platform**: {request.get('platform', 'twitter').title()}

---

## Tweet

{tweet_text}

---

## Actions

- [ ] Review tweet content above
- [ ] Edit if needed (must stay under 280 chars)
- [ ] Move to /Approved/ to post
- [ ] Delete this file to cancel

---

*Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by AI Employee*
"""

        draft_path.parent.mkdir(parents=True, exist_ok=True)
        draft_path.write_text(draft_content)
        logger.info(f"✓ Tweet draft created: {draft_filename}")

        return draft_path

    def draft_tweet(self, request_file: Path) -> Optional[Path]:
        """Main entry point: Draft a tweet from a request file"""

        if not request_file.exists():
            logger.error(f"Request file not found: {request_file}")
            return None

        # Check if already processed
        if request_file.name in self.processed_ids:
            logger.debug(f"⏭️ Skipping already-processed: {request_file.name}")
            return None

        logger.info(f"📱 Drafting tweet for: {request_file.name}")

        # Parse request
        request = self._parse_request(request_file)
        logger.debug(f"  Topic: {request.get('topic', 'N/A')}")

        # Generate tweet via OpenAI
        tweet_text, confidence = self._generate_tweet(request)

        # Create draft file
        draft_path = self._create_draft_file(request, tweet_text, confidence)

        # Mark as processed
        self._mark_processed(request_file.name)

        return draft_path

    def generate_scheduled_tweet(self, topic: str, context: str = "", style: str = "professional") -> Optional[Path]:
        """Generate a tweet without a request file (for scheduled tweets)"""

        request = {
            'filename': f"SCHEDULED_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'topic': topic,
            'style': style,
            'context': context,
            'hashtags': '',
            'platform': 'twitter'
        }

        logger.info(f"📱 Generating scheduled tweet: {topic}")

        tweet_text, confidence = self._generate_tweet(request)
        draft_path = self._create_draft_file(request, tweet_text, confidence)

        return draft_path


# CLI for testing
if __name__ == '__main__':
    import sys

    vault_path = os.getenv('VAULT_PATH', './vault')
    drafter = TweetDrafter(vault_path)

    if len(sys.argv) >= 2:
        # Draft from file
        request_file = Path(sys.argv[1])
        result = drafter.draft_tweet(request_file)
    else:
        # Generate scheduled tweet
        result = drafter.generate_scheduled_tweet(
            topic="AI automation and productivity",
            context="Weekly update on Digital FTE progress",
            style="professional"
        )

    if result:
        print(f"✅ Draft created: {result}")
    else:
        print("❌ Failed to create draft")
