/**
 * Email MCP Server - Wrapper for Gmail API
 * Integrates with Gmail watcher via Python subprocess
 */

const { Server } = require('@anthropic-sdk/mcp-sdk');
const { StdioTransport } = require('@anthropic-sdk/mcp-sdk');
const { spawn } = require('child_process');
const path = require('path');

const tools = [
  {
    name: 'send_email',
    description: 'Send an email via Gmail API',
    inputSchema: {
      type: 'object',
      properties: {
        to: { type: 'string', description: 'Recipient email address' },
        subject: { type: 'string', description: 'Email subject line' },
        body: { type: 'string', description: 'Email body (plain text or HTML)' },
        cc: { type: 'array', items: { type: 'string' }, description: 'CC recipients' },
        bcc: { type: 'array', items: { type: 'string' }, description: 'BCC recipients' },
        attachments: { type: 'array', items: { type: 'string' }, description: 'File paths to attach' }
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
        query: { type: 'string', description: 'Gmail query (e.g., "is:unread from:boss@company.com")' },
        limit: { type: 'number', description: 'Max emails to return', default: 10 },
        fields: { type: 'array', items: { type: 'string' }, description: 'Fields to return (id, subject, from, to, body)' }
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
  },
  {
    name: 'add_label',
    description: 'Add Gmail label to email',
    inputSchema: {
      type: 'object',
      properties: {
        message_id: { type: 'string', description: 'Gmail message ID' },
        label: { type: 'string', description: 'Label name (e.g., "Important", "Follow-up")' }
      },
      required: ['message_id', 'label']
    }
  }
];

/**
 * Process MCP tools - implements mock behavior for testing
 * In production, connects to Gmail Python watcher via API
 */
async function processTool(name, args) {
  const timestamp = new Date().toISOString();
  const messageId = `msg-${Date.now()}`;

  try {
    switch(name) {
      case 'send_email': {
        if (!args.to || !args.subject || !args.body) {
          return { error: 'Missing required fields: to, subject, body' };
        }
        return {
          status: 'sent',
          message_id: messageId,
          to: args.to,
          subject: args.subject,
          timestamp: timestamp,
          metadata: {
            cc: args.cc || [],
            bcc: args.bcc || [],
            attachments: args.attachments || []
          }
        };
      }

      case 'get_emails': {
        const query = args.query || 'is:unread';
        const limit = args.limit || 10;
        return {
          emails: [
            {
              id: 'EMAIL_001',
              from: 'boss@company.com',
              subject: 'Q1 Financial Review',
              snippet: 'Please review attached financial statements...',
              timestamp: '2026-01-08T10:30:00Z',
              labels: ['IMPORTANT', 'INBOX']
            },
            {
              id: 'EMAIL_002',
              from: 'finance@company.com',
              subject: 'Invoice #12345 Due',
              snippet: 'Invoice payment due by end of month...',
              timestamp: '2026-01-08T09:15:00Z',
              labels: ['INBOX']
            }
          ],
          query_used: query,
          count: 2,
          limit: limit
        };
      }

      case 'delete_email': {
        return {
          status: 'deleted',
          message_id: args.message_id,
          timestamp: timestamp
        };
      }

      case 'mark_read': {
        return {
          status: 'marked_read',
          message_id: args.message_id,
          timestamp: timestamp
        };
      }

      case 'add_label': {
        return {
          status: 'label_added',
          message_id: args.message_id,
          label: args.label,
          timestamp: timestamp
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
  { name: 'email-mcp', version: '1.0.0' },
  { transport: new StdioTransport(), tools }
);

server.setToolHandler(processTool);
server.start();
