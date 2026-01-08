/**
 * Twitter/X MCP - Tweet posting
 */

// TODO: Implement tweepy wrapper
const tools = [
  {
    name: 'post_tweet',
    description: 'Post a tweet',
    inputSchema: {
      type: 'object',
      properties: {
        text: { type: 'string' },
        reply_to: { type: 'string' }
      },
      required: ['text']
    }
  },
  {
    name: 'get_metrics',
    description: 'Get Twitter metrics'
  }
];

module.exports = { tools };
