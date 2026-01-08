/**
 * Meta Social MCP - Facebook & Instagram posting
 */

// TODO: Implement Meta Graph API wrapper
const tools = [
  {
    name: 'post_to_facebook',
    description: 'Post to Facebook page',
    inputSchema: {
      type: 'object',
      properties: {
        message: { type: 'string' },
        image_url: { type: 'string' }
      },
      required: ['message']
    }
  },
  {
    name: 'post_to_instagram',
    description: 'Post to Instagram',
    inputSchema: {
      type: 'object',
      properties: {
        caption: { type: 'string' },
        image_url: { type: 'string' }
      },
      required: ['caption', 'image_url']
    }
  },
  {
    name: 'get_engagement',
    description: 'Get engagement metrics'
  }
];

module.exports = { tools };
