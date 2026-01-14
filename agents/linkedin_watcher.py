"""LinkedIn API - Post to LinkedIn"""
import os
import json
import logging
import requests
from pathlib import Path
from datetime import datetime, timezone

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LinkedInAPI:
    """LinkedIn API for posting text and links"""

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.api_version = "v2"
        self.base_url = f"https://api.linkedin.com/{self.api_version}"

        if not self.access_token:
            logger.warning("⚠️ LINKEDIN_ACCESS_TOKEN not set")
        else:
            logger.info(f"✓ LinkedIn API initialized")

    def _get_headers(self):
        """Get request headers with auth"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def get_profile(self) -> dict:
        """Get authenticated user's profile"""
        try:
            headers = self._get_headers()
            response = requests.get(
                "https://api.linkedin.com/v2/userinfo",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch profile: {e}")
            raise

    def post_text(self, text: str) -> dict:
        """Post text to LinkedIn feed"""
        if not self.access_token:
            raise RuntimeError("LinkedIn access token not configured")

        try:
            # Get profile to get ID
            profile = self.get_profile()
            profile_id = profile.get('sub')

            if not profile_id:
                raise ValueError("Could not get user profile ID")

            headers = self._get_headers()

            # LinkedIn REST API for text posts
            url = f"{self.base_url}/ugcPosts"

            payload = {
                "author": f"urn:li:person:{profile_id}",
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

            response = requests.post(url, json=payload, headers=headers)

            if response.status_code not in [200, 201]:
                error_msg = response.text
                logger.error(f"LinkedIn API error: {response.status_code} - {error_msg}")
                raise RuntimeError(f"LinkedIn API error: {response.status_code}")

            result = response.json()
            post_id = result.get('id', 'unknown')

            logger.info(f"✅ Text posted to LinkedIn")
            logger.info(f"   Post ID: {post_id}")

            return {
                'id': post_id,
                'type': 'text',
                'text': text[:200]
            }

        except Exception as e:
            logger.error(f"Failed to post text to LinkedIn: {e}")
            raise

    def post_with_link(self, text: str, url: str) -> dict:
        """Post text with link to LinkedIn feed"""
        if not self.access_token:
            raise RuntimeError("LinkedIn access token not configured")

        try:
            # Get profile to get ID
            profile = self.get_profile()
            profile_id = profile.get('sub')

            if not profile_id:
                raise ValueError("Could not get user profile ID")

            headers = self._get_headers()

            # LinkedIn REST API for posts with links
            api_url = f"{self.base_url}/ugcPosts"

            payload = {
                "author": f"urn:li:person:{profile_id}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": text
                        },
                        "shareMediaCategory": "ARTICLE",
                        "media": [
                            {
                                "status": "READY",
                                "originalUrl": url
                            }
                        ]
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }

            response = requests.post(api_url, json=payload, headers=headers)

            if response.status_code not in [200, 201]:
                error_msg = response.text
                logger.error(f"LinkedIn API error: {response.status_code} - {error_msg}")
                raise RuntimeError(f"LinkedIn API error: {response.status_code}")

            result = response.json()
            post_id = result.get('id', 'unknown')

            logger.info(f"✅ Link posted to LinkedIn")
            logger.info(f"   Post ID: {post_id}")
            logger.info(f"   URL: {url}")

            return {
                'id': post_id,
                'type': 'link',
                'text': text[:200],
                'url': url
            }

        except Exception as e:
            logger.error(f"Failed to post link to LinkedIn: {e}")
            raise


if __name__ == '__main__':
    access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
    if not access_token:
        print("Error: LINKEDIN_ACCESS_TOKEN not set in environment")
        exit(1)

    api = LinkedInAPI(access_token)

    # Test post
    try:
        result = api.post_text("Testing LinkedIn API integration! 🚀")
        print(f"Success: {result}")
    except Exception as e:
        print(f"Error: {e}")
