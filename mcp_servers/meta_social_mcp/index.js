/**
 * Meta Social MCP - Facebook & Instagram management
 * Integrates with Meta Graph API for content posting and analytics
 */

const { Server } = require('@anthropic-sdk/mcp-sdk');
const { StdioTransport } = require('@anthropic-sdk/mcp-sdk');

const tools = [
  {
    name: 'post_to_facebook',
    description: 'Post content to Facebook business page',
    inputSchema: {
      type: 'object',
      properties: {
        page_id: { type: 'string', description: 'Facebook page ID' },
        message: { type: 'string', description: 'Post message/caption' },
        image_url: { type: 'string', description: 'Image URL (optional)' },
        link: { type: 'string', description: 'External link (optional)' },
        published: { type: 'boolean', description: 'Publish immediately or as draft', default: true }
      },
      required: ['message']
    }
  },
  {
    name: 'post_to_instagram',
    description: 'Post content to Instagram business account',
    inputSchema: {
      type: 'object',
      properties: {
        business_account_id: { type: 'string', description: 'Instagram business account ID' },
        caption: { type: 'string', description: 'Post caption' },
        image_url: { type: 'string', description: 'Image URL' },
        hashtags: { type: 'array', items: { type: 'string' }, description: 'Hashtags' },
        published: { type: 'boolean', description: 'Publish immediately', default: true }
      },
      required: ['caption', 'image_url']
    }
  },
  {
    name: 'get_engagement',
    description: 'Get engagement metrics for posts',
    inputSchema: {
      type: 'object',
      properties: {
        account_type: { type: 'string', enum: ['facebook', 'instagram'], description: 'Account type' },
        period: { type: 'string', enum: ['last_7_days', 'last_30_days', 'all_time'], default: 'last_7_days' },
        post_id: { type: 'string', description: 'Specific post ID (optional)' }
      }
    }
  },
  {
    name: 'schedule_post',
    description: 'Schedule post for future publication',
    inputSchema: {
      type: 'object',
      properties: {
        platform: { type: 'string', enum: ['facebook', 'instagram'], description: 'Target platform' },
        content: { type: 'string', description: 'Post content' },
        scheduled_time: { type: 'string', description: 'Publish time (ISO 8601)' },
        media_urls: { type: 'array', items: { type: 'string' }, description: 'Media attachments' }
      },
      required: ['platform', 'content', 'scheduled_time']
    }
  },
  {
    name: 'get_audience_insights',
    description: 'Get audience demographics and insights',
    inputSchema: {
      type: 'object',
      properties: {
        account_type: { type: 'string', enum: ['facebook', 'instagram'] },
        metrics: { type: 'array', items: { type: 'string' }, description: 'Specific metrics (age, gender, location, interests)' }
      }
    }
  },
  {
    name: 'delete_post',
    description: 'Delete a published post',
    inputSchema: {
      type: 'object',
      properties: {
        post_id: { type: 'string', description: 'Post ID to delete' }
      },
      required: ['post_id']
    }
  }
];

const https = require('https');

// Get credentials from environment
const PAGE_ID = process.env.META_PAGE_ID;
const ACCESS_TOKEN = process.env.META_ACCESS_TOKEN;

// Helper to call Meta Graph API
function callMetaAPI(endpoint, method = 'GET', data = null) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'graph.instagram.com',
      path: `/${endpoint}?access_token=${ACCESS_TOKEN}`,
      method: method,
      headers: { 'Content-Type': 'application/json' }
    };

    const req = https.request(options, (res) => {
      let body = '';
      res.on('data', (chunk) => body += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(body));
        } catch (e) {
          reject(e);
        }
      });
    });

    req.on('error', reject);
    if (data) req.write(JSON.stringify(data));
    req.end();
  });
}

/**
 * Process Meta Social MCP tools - Calls Graph API
 */
async function processTool(name, args) {
  const timestamp = new Date().toISOString();

  try {
    switch(name) {
      case 'post_to_facebook': {
        const result = await callMetaAPI(
          `${PAGE_ID}/feed`,
          'POST',
          {
            message: args.message,
            link: args.link || undefined,
            published: args.published !== false
          }
        );
        return {
          status: 'posted',
          post_id: result.id,
          platform: 'facebook',
          message: args.message,
          url: `https://facebook.com/${result.id}`,
          created_at: timestamp
        };
      }

      case 'post_to_instagram': {
        const result = await callMetaAPI(
          `${PAGE_ID}/media`,
          'POST',
          {
            image_url: args.image_url,
            caption: args.caption,
            hashtags: args.hashtags || []
          }
        );
        return {
          status: 'posted',
          post_id: result.id,
          platform: 'instagram',
          caption: args.caption,
          url: `https://instagram.com/p/${result.id}`,
          created_at: timestamp
        };
      }

      case 'get_engagement': {
        const metric = args.post_id ? `${args.post_id}/insights` : `${PAGE_ID}/insights`;
        const result = await callMetaAPI(metric);
        return {
          period: args.period || 'last_7_days',
          platform: args.account_type || 'facebook',
          metrics: result.data || {},
          updated_at: timestamp
        };
      }

      case 'schedule_post': {
        const scheduled = Math.floor(new Date(args.scheduled_time).getTime() / 1000);
        const result = await callMetaAPI(
          `${PAGE_ID}/feed`,
          'POST',
          {
            message: args.content,
            scheduled_publish_time: scheduled,
            published: false
          }
        );
        return {
          status: 'scheduled',
          post_id: result.id,
          platform: args.platform,
          scheduled_time: args.scheduled_time,
          created_at: timestamp
        };
      }

      case 'get_audience_insights': {
        const result = await callMetaAPI(`${PAGE_ID}/insights?metric=page_fans`);
        return {
          account_type: args.account_type,
          insights: result.data || [],
          updated_at: timestamp
        };
      }

      case 'delete_post': {
        await callMetaAPI(args.post_id, 'DELETE');
        return {
          status: 'deleted',
          post_id: args.post_id,
          deleted_at: timestamp
        };
      }

      default:
        return { error: `Unknown tool: ${name}` };
    }
  } catch (error) {
    return { error: `Tool execution failed: ${error.message}` };
  }
}

const server = new Server(
  { name: 'meta-social-mcp', version: '1.0.0' },
  { transport: new StdioTransport(), tools }
);

server.setToolHandler(processTool);
server.start();

module.exports = { tools };
