/**
 * Xero MCP Server - Accounting operations
 */

// TODO: Implement xero-python SDK wrapper
const tools = [
  {
    name: 'create_invoice',
    description: 'Create invoice in Xero',
    inputSchema: {
      type: 'object',
      properties: {
        contact_name: { type: 'string' },
        amount: { type: 'number' },
        description: { type: 'string' },
        due_date: { type: 'string' }
      },
      required: ['contact_name', 'amount', 'description']
    }
  },
  {
    name: 'log_transaction',
    description: 'Log transaction to Xero',
    inputSchema: {
      type: 'object',
      properties: {
        amount: { type: 'number' },
        description: { type: 'string' },
        account: { type: 'string' }
      },
      required: ['amount', 'description']
    }
  },
  {
    name: 'get_balance',
    description: 'Get current account balance'
  }
];

module.exports = { tools };
