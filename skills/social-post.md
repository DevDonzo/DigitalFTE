# Social Post Agent Skill

**Skill ID**: `social-post`
**Type**: Autonomous Content Generation / Social Media
**Tier**: Gold
**Dependencies**: OpenAI API, Twitter API, Meta API (optional)

## Purpose

Enable the AI Employee to autonomously generate social media content (tweets, Facebook/Instagram posts) with AI-powered drafting and human-in-the-loop approval before posting.

## Architecture

```
Tweet/Post Request
    |
Tweet Drafter reads:
  |-- Request content (topic, context, style)
  |-- Company_Handbook.md (brand voice)
  +-- Previous posts (avoid duplicates)
    |
OpenAI generates content:
  |-- Understands topic intent
  |-- Applies brand guidelines
  |-- Drafts engaging content
  +-- Respects character limits
    |
Creates Pending_Approval/
  |-- Original request
  |-- AI draft with reasoning
  |-- Character count
  +-- Hashtag suggestions
    |
Human reviews (optional edit)
    |
Approval triggers Post API
    |
Posted + logged to audit trail
```

## Implementation

### Tweet Drafter
- **File**: `utils/tweet_drafter.py`
- **Class**: `TweetDrafter`
- **AI Model**: OpenAI GPT-3.5-turbo

### Orchestrator Integration
- **File**: `scripts/orchestrator.py`
- **Method**: `_process_inbox()` - Routes TWEET/SOCIAL files to TweetDrafter
- **Method**: `_execute_post()` - Posts to Twitter via OAuth 1.0a
- **Method**: `_call_twitter_api()` - Direct Twitter API v2 call

### Twitter MCP Server (Optional)
- **File**: `mcp_servers/twitter_mcp/index.js`
- **Tools**: post_tweet, get_tweet_metrics, schedule_tweet

## Capabilities

### Content Generation
- Generate tweets within 280 character limit
- Create engaging hooks and calls-to-action
- Add relevant hashtags
- Match brand voice from Company_Handbook.md

### Platform Support
- Twitter/X (implemented via OAuth 1.0a)
- Facebook (pending Meta API credentials)
- Instagram (pending Meta API credentials)

### Safety Features
- Human approval required before posting
- Duplicate detection
- Content moderation flags
- Audit logging of all posts

## Usage Flow

1. **Request created** -> `vault/Needs_Action/TWEET_REQUEST_*.md`
2. **Orchestrator detects** -> Triggers TweetDrafter
3. **OpenAI drafts** -> Generates content + reasoning
4. **Creates approval file** -> `vault/Pending_Approval/POST_TWEET_*.md`
5. **Human reviews** -> Edit if needed
6. **Move to Approved** -> `vault/Approved/POST_*.md`
7. **Orchestrator posts** -> Calls Twitter API v2
8. **Logged** -> `vault/Done/` + `vault/Logs/posts_sent.jsonl`

## File Format (Request)

```markdown
---
type: tweet_request
topic: product launch announcement
style: professional
---

## Topic
Announce the launch of our new AI assistant feature

## Context
We've been working on this for 3 months. Key features: auto-replies, smart scheduling, voice commands.

## Hashtags (optional)
#AI #ProductLaunch #Innovation
```

## File Format (Draft)

```markdown
---
type: social_post
platform: twitter
ai_generated: true
confidence: 0.92
created: 2026-01-10T10:47:00Z
---

## Tweet

Excited to announce our new AI assistant feature! Auto-replies, smart scheduling, and voice commands - all designed to save you time. #AI #ProductLaunch

## AI Analysis

- Character count: 156/280
- Hashtags: 2
- Call-to-action: Implicit (announcement)
- Tone: Professional, enthusiastic

## Actions

- [ ] Edit tweet above
- [ ] Move to /Approved/ to post
- [ ] Reject
```

## Configuration

In `Company_Handbook.md`:

```yaml
social_media:
  platforms:
    - twitter
    - facebook
    - instagram

  brand_voice: "Professional but approachable, innovative, helpful"

  posting_rules:
    - No controversial topics
    - Include call-to-action when relevant
    - Use 1-3 hashtags per post
    - Avoid posting more than 3x/day

  approval_required: true
```

## API Configuration

In `.env`:

```
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
```

## Metrics Tracked

- Posts per platform per day
- Engagement rate (if metrics endpoint used)
- AI draft acceptance rate
- Human edit frequency
- Post timing optimization

## Status

- Twitter/X: IMPLEMENTED
- Facebook: Pending credentials
- Instagram: Pending credentials
