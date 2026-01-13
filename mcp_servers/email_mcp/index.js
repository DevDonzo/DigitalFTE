#!/usr/bin/env node

/**
 * Email MCP Server - Real Gmail API Integration
 * Wraps google-auth-oauthlib and google-api-python-client
 */

const { Server } = require('@anthropic-sdk/mcp-sdk');
const { StdioTransport } = require('@anthropic-sdk/mcp-sdk');
const axios = require('axios');
const path = require('path');
const fs = require('fs');
const os = require('os');

// Configuration
const GMAIL_API_BASE = 'https://gmail.googleapis.com/gmail/v1/users/me';

const tools = [
  {
    name: 'send_email',
    description: 'Send an email via Gmail API',
    inputSchema: {
      type: 'object',
      properties: {
        to: { type: 'string', description: 'Recipient email address' },
        subject: { type: 'string', description: 'Email subject line' },
        body: { type: 'string', description: 'Email body (plain text)' },
        cc: { type: 'array', items: { type: 'string' }, description: 'CC recipients' },
        bcc: { type: 'array', items: { type: 'string' }, description: 'BCC recipients' }
      },
      required: ['to', 'subject', 'body']
    }
  },
  {
    name: 'get_emails',
    description: 'Retrieve emails matching criteria',
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string', description: 'Gmail query (e.g., "is:unread")' },
        limit: { type: 'number', description: 'Max emails to return', default: 10 }
      }
    }
  },
  {
    name: 'delete_email',
    description: 'Delete an email permanently',
    inputSchema: {
      type: 'object',
      properties: {
        message_id: { type: 'string', description: 'Gmail message ID' }
      },
      required: ['message_id']
    }
  },
  {
    name: 'mark_read',
    description: 'Mark email as read',
    inputSchema: {
      type: 'object',
      properties: {
        message_id: { type: 'string', description: 'Gmail message ID' }
      },
      required: ['message_id']
    }
  }
];

/**
 * Get access token from credentials file or environment
 */
function getAccessToken() {
  const credPath = process.env.GMAIL_CREDENTIALS_PATH ||
    process.env.GMAIL_CREDENTIALS ||
    path.join(os.homedir(), '.gmail_token.json');

  if (!fs.existsSync(credPath)) {
    console.error('Warning: Gmail credentials not found at', credPath);
    return null;
  }

  try {
    const creds = JSON.parse(fs.readFileSync(credPath, 'utf8'));
    return creds.access_token || creds.token;
  } catch (e) {
    console.error('Error reading credentials:', e.message);
    return null;
  }
}

/**
 * Process Email MCP tools - Real Gmail API calls
 */
async function processTool(name, args) {
  const token = getAccessToken();

  if (!token) {
    return { error: 'Gmail credentials not configured. Run auth/gmail.py to authenticate.' };
  }

  try {
    switch(name) {
      case 'send_email': {
        if (!args.to || !args.subject || !args.body) {
          return { error: 'Missing required fields: to, subject, body' };
        }

        // Create MIME message
        const message = [
          `From: me`,
          `To: ${args.to}`,
          `${args.cc ? `Cc: ${args.cc.join(',')}` : ''}`,
          `${args.bcc ? `Bcc: ${args.bcc.join(',')}` : ''}`,
          `Subject: ${args.subject}`,
          '',
          args.body
        ].filter(l => l).join('\r\n');

        const encodedMessage = Buffer.from(message)
          .toString('base64')
          .replace(/\+/g, '-')
          .replace(/\//g, '_');

        const response = await axios.post(
          `${GMAIL_API_BASE}/messages/send`,
          { raw: encodedMessage },
          { headers: { Authorization: `Bearer ${token}` } }
        );

        return {
          status: 'sent',
          message_id: response.data.id,
          to: args.to,
          subject: args.subject,
          timestamp: new Date().toISOString()
        };
      }

      case 'get_emails': {
        const query = args.query || 'is:unread';
        const limit = args.limit || 10;

        const response = await axios.get(
          `${GMAIL_API_BASE}/messages`,
          {
            params: { q: query, maxResults: limit },
            headers: { Authorization: `Bearer ${token}` }
          }
        );

        if (!response.data.messages) {
          return { emails: [], count: 0, limit };
        }

        // Get details for each message
        const emails = await Promise.all(
          response.data.messages.slice(0, limit).map(async (msg) => {
            try {
              const detail = await axios.get(
                `${GMAIL_API_BASE}/messages/${msg.id}`,
                { headers: { Authorization: `Bearer ${token}` } }
              );
              const headers = detail.data.payload?.headers || [];
              const fromHeader = headers.find(h => h.name === 'From') || {};
              const subjectHeader = headers.find(h => h.name === 'Subject') || {};

              return {
                id: msg.id,
                from: fromHeader.value || 'unknown',
                subject: subjectHeader.value || '(no subject)',
                timestamp: new Date(parseInt(detail.data.internalDate)).toISOString()
              };
            } catch (e) {
              return { id: msg.id, error: e.message };
            }
          })
        );

        return {
          emails,
          count: emails.length,
          limit,
          query_used: query
        };
      }

      case 'delete_email': {
        await axios.delete(
          `${GMAIL_API_BASE}/messages/${args.message_id}`,
          { headers: { Authorization: `Bearer ${token}` } }
        );

        return {
          status: 'deleted',
          message_id: args.message_id,
          timestamp: new Date().toISOString()
        };
      }

      case 'mark_read': {
        await axios.post(
          `${GMAIL_API_BASE}/messages/${args.message_id}/modify`,
          { removeLabelIds: ['UNREAD'] },
          { headers: { Authorization: `Bearer ${token}` } }
        );

        return {
          status: 'marked_read',
          message_id: args.message_id,
          timestamp: new Date().toISOString()
        };
      }

      default:
        return { error: `Unknown tool: ${name}` };
    }
  } catch (error) {
    console.error(`Email MCP error for ${name}:`, error.message);
    return {
      error: `Tool execution failed: ${error.message}`,
      status: 'failed'
    };
  }
}

const server = new Server(
  { name: 'email-mcp', version: '1.0.0' },
  {
    transport: new StdioTransport(),
    tools
  }
);

server.setToolHandler(processTool);
server.start();

console.error('✅ Email MCP Server started (Gmail API integration)');
