# Social Media Auto-Posting Guide

## How to Queue Posts

Create files in this folder to auto-post to Twitter, Facebook, or LinkedIn.

### Twitter/X Post

**File**: `vault/Social_Media/TWEET_[name].md`

```
---
type: social_post
platform: twitter
content: Your tweet text here (max 280 chars)
---

## Tweet Content

Your tweet here.
```

### Facebook Post

**File**: `vault/Social_Media/FACEBOOK_[name].md`

```
---
type: social_post
platform: facebook
content: Your Facebook post here
---

## Post Content

Your post here.
```

### LinkedIn Post

**File**: `vault/Social_Media/LINKEDIN_[name].md`

```
---
type: social_post
platform: linkedin
content: Your LinkedIn post here
---

## Post Content

Your post here.
```

## Workflow

1. Create file in `vault/Social_Media/`
2. Move to `vault/Approved/` when ready
3. Orchestrator auto-posts
4. Result logged to `vault/Logs/`

## Auto-Post Rules (in Company_Handbook.md)

- Scheduled posts auto-post immediately
- Real-time posts require human approval
- All posts logged with timestamp and engagement metrics
