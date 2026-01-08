/**
 * Email MCP Server - Wrapper for Gmail API
 */

const { Server } = require('@anthropic-sdk/mcp-sdk');
const { StdioTransport } = require('@anthropic-sdk/mcp-sdk');

// TODO: Implement real Gmail API calls
const tools = [
  {
    name: 'send_email',
    description: 'Send an email via Gmail',
    inputSchema: {
      type: 'object',
      properties: {
        to: { type: 'string', description: 'Recipient email' },
        subject: { type: 'string', description: 'Email subject' },
        body: { type: 'string', description: 'Email body (HTML ok)' },
        cc: { type: 'array', items: { type: 'string' } }
      },
      required: ['to', 'subject', 'body']
    }
  },
  {
    name: 'get_emails',
    description: 'Get unread emails',
    inputSchema: {
      type: 'object',
      properties: {
        limit: { type: 'number', default: 10 }
      }
    }
  }
];

async function processTool(name, args) {
  switch(name) {
    case 'send_email':
      // TODO: Call google-api-python-client
      return { status: 'sent', message_id: 'fake-id' };
    case 'get_emails':
      return { emails: [] };
    default:
      return { error: 'Unknown tool' };
  }
}

const server = new Server({ name: 'email-mcp', version: '1.0.0' }, {
  transport: new StdioTransport(),
  tools
});

server.setToolHandler(processTool);
server.start();
