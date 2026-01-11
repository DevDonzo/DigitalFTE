# Meta Social MCP Server

Provides Claude Code with tools to post to Facebook and Instagram using the Meta Graph API.

## Features

- **Post to Facebook Page** - Immediate or scheduled posting
- **Post to Instagram Business Account** - Share content to Instagram
- **Get Engagement Metrics** - Fetch likes, impressions, reach, and followers
- **Schedule Posts** - Schedule Facebook posts for future publication
- **Get Page/Media Insights** - Detailed analytics per post

## Installation

```bash
npm install
```

## Configuration

Set environment variables in `.env`:

```
FACEBOOK_ACCESS_TOKEN=your_access_token_here
FACEBOOK_PAGE_ID=your_page_id_here
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_instagram_business_account_id
```

## Usage

### Via Node.js

```bash
FACEBOOK_ACCESS_TOKEN=token FACEBOOK_PAGE_ID=123 node index.js
```

### Via Orchestrator

The orchestrator automatically calls this MCP for Facebook/Instagram posts.

## Tools Available

### post_facebook
Post text content to Facebook Page

```json
{
  "tool": "post_facebook",
  "input": {
    "page_id": "123456",
    "message": "Hello Facebook!",
    "image_url": "https://example.com/image.jpg",
    "link_url": "https://example.com"
  }
}
```

### post_instagram
Post content (with image) to Instagram Business Account

```json
{
  "tool": "post_instagram",
  "input": {
    "account_id": "123456",
    "caption": "Hello Instagram!",
    "image_url": "https://example.com/image.jpg",
    "media_type": "IMAGE"
  }
}
```

### schedule_facebook
Schedule a Facebook post for future publication

```json
{
  "tool": "schedule_facebook",
  "input": {
    "page_id": "123456",
    "message": "Scheduled post",
    "publish_time": "2026-01-20T14:00:00Z",
    "image_url": "https://example.com/image.jpg"
  }
}
```

### get_instagram_insights
Get Instagram account metrics

```json
{
  "tool": "get_instagram_insights",
  "input": {
    "account_id": "123456",
    "metric": "impressions"
  }
}
```

Valid metrics:
- `impressions` - Total post impressions
- `reach` - Unique people reached
- `profile_views` - Profile view count
- `follower_count` - Total followers

### get_media_insights
Get engagement metrics for a specific post

```json
{
  "tool": "get_media_insights",
  "input": {
    "media_id": "post_id_123"
  }
}
```

### get_page_insights
Get Facebook page metrics

```json
{
  "tool": "get_page_insights",
  "input": {
    "page_id": "123456"
  }
}
```

### check_auth
Verify authentication status

```json
{
  "tool": "check_auth",
  "input": {}
}
```

## Getting API Credentials

### Facebook Access Token

1. Go to https://developers.facebook.com/
2. Create/select an app
3. Go to Settings → Basic and save App ID + Secret
4. Generate User Access Token via Tools → Access Token Debugger
5. Save as `FACEBOOK_ACCESS_TOKEN` in `.env`

### Page ID

1. Go to your Facebook Page
2. Click Settings → About
3. Find "Page ID" in left sidebar
4. Save as `FACEBOOK_PAGE_ID`

### Instagram Business Account ID

1. Go to https://business.instagram.com
2. Navigate to Settings → Instagram Accounts
3. Copy the Instagram Business Account ID
4. Save as `INSTAGRAM_BUSINESS_ACCOUNT_ID`

## Error Handling

The server validates:
- Access token validity
- Required account IDs
- API response status codes
- JSON parsing errors

All errors are returned with descriptive messages:

```json
{
  "success": false,
  "error": "Error description",
  "platform": "facebook"
}
```

## Testing

```bash
# Check authentication
echo '{"tool": "check_auth", "input": {}}' | node index.js

# Post to Facebook (requires valid credentials)
echo '{"tool": "post_facebook", "input": {"page_id": "123", "message": "Test"}}' | node index.js
```

## Logs

All posts are logged to `vault/Logs/posts_sent.jsonl` with:
- Timestamp
- Platform (facebook/instagram)
- Post ID
- Content
- Direct link to post

## Troubleshooting

### Invalid Access Token
- Check token hasn't expired
- Regenerate at https://developers.facebook.com/
- Verify token has `pages_manage_posts` permission

### Page ID Not Found
- Ensure `FACEBOOK_PAGE_ID` is correct
- Verify your app has access to the page
- Check page admin settings

### Instagram Account Not Found
- Ensure business account is linked to Meta Business Account
- Verify `INSTAGRAM_BUSINESS_ACCOUNT_ID` is correct
- Check account is in Professional Mode

## API Reference

- Facebook Graph API: https://developers.facebook.com/docs/graph-api
- Instagram Graph API: https://developers.facebook.com/docs/instagram-api
