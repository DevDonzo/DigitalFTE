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


# LinkedInWatcher class removed - orchestrator.py handles posting via LinkedInAPI
