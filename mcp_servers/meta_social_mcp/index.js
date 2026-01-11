#!/usr/bin/env node

/**
 * Meta Social MCP Server
 * Provides Claude Code with tools to post to Facebook/Instagram
 */

const axios = require('axios');

// Configuration from environment
const FACEBOOK_ACCESS_TOKEN = process.env.FACEBOOK_ACCESS_TOKEN || '';
const INSTAGRAM_BUSINESS_ACCOUNT_ID = process.env.INSTAGRAM_BUSINESS_ACCOUNT_ID || '';
const FACEBOOK_PAGE_ID = process.env.FACEBOOK_PAGE_ID || '';

const API_VERSION = 'v18.0';
const GRAPH_API_BASE = `https://graph.instagram.com/${API_VERSION}`;
const FACEBOOK_GRAPH_BASE = `https://graph.facebook.com/${API_VERSION}`;

/**
 * Post to Facebook Page
 */
async function postToFacebook(pageId, message, imageUrl = null, linkUrl = null) {
  try {
    const data = {
      message: message,
      access_token: FACEBOOK_ACCESS_TOKEN
    };

    if (imageUrl) {
      data.picture = imageUrl;
      data.link = linkUrl || imageUrl;
    }

    const response = await axios.post(
      `${FACEBOOK_GRAPH_BASE}/${pageId}/feed`,
      data
    );

    return {
      success: true,
      post_id: response.data.id,
      platform: 'facebook',
      message: `Posted to Facebook successfully (ID: ${response.data.id})`,
      timestamp: new Date().toISOString()
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      platform: 'facebook'
    };
  }
}

/**
 * Post to Instagram Business Account
 */
async function postToInstagram(businessAccountId, caption, imageUrl, mediaType = 'IMAGE') {
  try {
    // Step 1: Create media container
    const containerResponse = await axios.post(
      `${GRAPH_API_BASE}/${businessAccountId}/media`,
      {
        image_url: imageUrl,
        caption: caption,
        media_type: mediaType,
        access_token: FACEBOOK_ACCESS_TOKEN
      }
    );

    const containerId = containerResponse.data.id;

    // Step 2: Publish media container
    const publishResponse = await axios.post(
      `${GRAPH_API_BASE}/${businessAccountId}/media_publish`,
      {
        creation_id: containerId,
        access_token: FACEBOOK_ACCESS_TOKEN
      }
    );

    return {
      success: true,
      post_id: publishResponse.data.id,
      platform: 'instagram',
      message: `Posted to Instagram successfully (ID: ${publishResponse.data.id})`,
      timestamp: new Date().toISOString()
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      platform: 'instagram'
    };
  }
}

/**
 * Get Instagram Insights (engagement metrics)
 */
async function getInstagramInsights(businessAccountId, metric = 'impressions') {
  try {
    const validMetrics = ['impressions', 'reach', 'profile_views', 'follower_count'];
    
    if (!validMetrics.includes(metric)) {
      metric = 'impressions';
    }

    const response = await axios.get(
      `${GRAPH_API_BASE}/${businessAccountId}/insights`,
      {
        params: {
          metric: metric,
          period: 'day',
          access_token: FACEBOOK_ACCESS_TOKEN
        }
      }
    );

    return {
      success: true,
      metric: metric,
      data: response.data.data,
      platform: 'instagram',
      timestamp: new Date().toISOString()
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      metric: metric
    };
  }
}

/**
 * Get Instagram Media Insights (for specific post)
 */
async function getMediaInsights(mediaId) {
  try {
    const response = await axios.get(
      `${GRAPH_API_BASE}/${mediaId}/insights`,
      {
        params: {
          metric: 'engagement,impressions,reach,saved',
          access_token: FACEBOOK_ACCESS_TOKEN
        }
      }
    );

    return {
      success: true,
      media_id: mediaId,
      insights: response.data.data,
      platform: 'instagram',
      timestamp: new Date().toISOString()
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      media_id: mediaId
    };
  }
}

/**
 * Schedule post to Facebook (future publication)
 */
async function scheduleToFacebook(pageId, message, publishTime, imageUrl = null) {
  try {
    const data = {
      message: message,
      scheduled_publish_time: Math.floor(new Date(publishTime).getTime() / 1000),
      access_token: FACEBOOK_ACCESS_TOKEN
    };

    if (imageUrl) {
      data.picture = imageUrl;
    }

    const response = await axios.post(
      `${FACEBOOK_GRAPH_BASE}/${pageId}/feed`,
      data
    );

    return {
      success: true,
      post_id: response.data.id,
      platform: 'facebook',
      scheduled_for: publishTime,
      message: `Post scheduled for ${publishTime}`,
      timestamp: new Date().toISOString()
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      platform: 'facebook'
    };
  }
}

/**
 * Get page insights (engagement stats)
 */
async function getPageInsights(pageId) {
  try {
    const response = await axios.get(
      `${FACEBOOK_GRAPH_BASE}/${pageId}/insights`,
      {
        params: {
          metric: 'page_views,page_impressions,page_fans,post_impressions',
          period: 'day',
          access_token: FACEBOOK_ACCESS_TOKEN
        }
      }
    );

    return {
      success: true,
      page_id: pageId,
      insights: response.data.data,
      platform: 'facebook',
      timestamp: new Date().toISOString()
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      page_id: pageId
    };
  }
}

/**
 * Check authentication status
 */
async function checkAuth() {
  try {
    const response = await axios.get(
      `${FACEBOOK_GRAPH_BASE}/me`,
      {
        params: {
          access_token: FACEBOOK_ACCESS_TOKEN
        }
      }
    );

    return {
      authenticated: true,
      user_id: response.data.id,
      name: response.data.name
    };
  } catch (error) {
    return {
      authenticated: false,
      error: 'Invalid or expired access token'
    };
  }
}

/**
 * Main MCP Handler
 */
async function handleRequest(toolName, toolInput) {
  console.error(`[Meta Social MCP] Tool called: ${toolName}`);

  switch (toolName) {
    case 'post_facebook':
      return await postToFacebook(
        toolInput.page_id || FACEBOOK_PAGE_ID,
        toolInput.message,
        toolInput.image_url,
        toolInput.link_url
      );

    case 'post_instagram':
      return await postToInstagram(
        toolInput.account_id || INSTAGRAM_BUSINESS_ACCOUNT_ID,
        toolInput.caption,
        toolInput.image_url,
        toolInput.media_type || 'IMAGE'
      );

    case 'schedule_facebook':
      return await scheduleToFacebook(
        toolInput.page_id || FACEBOOK_PAGE_ID,
        toolInput.message,
        toolInput.publish_time,
        toolInput.image_url
      );

    case 'get_instagram_insights':
      return await getInstagramInsights(
        toolInput.account_id || INSTAGRAM_BUSINESS_ACCOUNT_ID,
        toolInput.metric
      );

    case 'get_media_insights':
      return await getMediaInsights(toolInput.media_id);

    case 'get_page_insights':
      return await getPageInsights(toolInput.page_id || FACEBOOK_PAGE_ID);

    case 'check_auth':
      return await checkAuth();

    default:
      return {
        success: false,
        error: `Unknown tool: ${toolName}`
      };
  }
}

/**
 * Start MCP Server
 */
async function startServer() {
  console.error('🚀 Meta Social MCP Server starting...');
  console.error(`📱 Instagram Account ID: ${INSTAGRAM_BUSINESS_ACCOUNT_ID || 'NOT SET'}`);
  console.error(`📘 Facebook Page ID: ${FACEBOOK_PAGE_ID || 'NOT SET'}`);
  console.error(`🔑 Access Token: ${FACEBOOK_ACCESS_TOKEN ? '✓ SET' : '✗ NOT SET'}`);

  // Check authentication on startup
  const auth = await checkAuth();
  if (auth.authenticated) {
    console.error(`✅ Authentication successful (${auth.name})`);
  } else {
    console.error(`⚠️  Authentication failed: ${auth.error}`);
  }

  console.error('Available tools:');
  console.error('  - post_facebook: Post to Facebook Page');
  console.error('  - post_instagram: Post to Instagram Business Account');
  console.error('  - schedule_facebook: Schedule Facebook post');
  console.error('  - get_instagram_insights: Get Instagram metrics');
  console.error('  - get_media_insights: Get metrics for specific post');
  console.error('  - get_page_insights: Get Facebook page metrics');
  console.error('  - check_auth: Verify authentication status');

  // Read stdin for MCP requests
  let inputBuffer = '';

  process.stdin.on('data', async (chunk) => {
    inputBuffer += chunk.toString();

    try {
      // Try to parse complete JSON objects
      const lines = inputBuffer.split('\n');
      inputBuffer = lines[lines.length - 1]; // Keep incomplete line

      for (let i = 0; i < lines.length - 1; i++) {
        if (lines[i].trim()) {
          const request = JSON.parse(lines[i]);
          const result = await handleRequest(request.tool, request.input || {});
          console.log(JSON.stringify(result));
        }
      }
    } catch (error) {
      // Invalid JSON, wait for more data
    }
  });

  process.stdin.on('end', () => {
    console.error('Meta Social MCP Server shutting down');
    process.exit(0);
  });
}

// Start server
startServer().catch(error => {
  console.error('❌ Fatal error:', error.message);
  process.exit(1);
});

module.exports = {
  postToFacebook,
  postToInstagram,
  scheduleToFacebook,
  getInstagramInsights,
  getMediaInsights,
  getPageInsights,
  checkAuth
};
