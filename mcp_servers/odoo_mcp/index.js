#!/usr/bin/env node

/**
 * Odoo MCP Server - Accounting & ERP Integration
 *
 * Provides MCP tools for interacting with Odoo Community Edition via JSON-RPC API
 * Supports: Invoice creation, bill entry, journal entries, account queries, reports
 */

import axios from 'axios';
import { config } from 'dotenv';

// Load environment variables
config();

const ODOO_URL = process.env.ODOO_URL || 'http://localhost:8069';
const ODOO_DB = process.env.ODOO_DB || 'gte';
const ODOO_USERNAME = process.env.ODOO_USERNAME || 'admin';
const ODOO_PASSWORD = process.env.ODOO_PASSWORD || 'admin';

// Odoo JSON-RPC endpoint
const ENDPOINT = `${ODOO_URL}/jsonrpc`;

let sessionId = null;
let userId = null;

// ============================================================================
// TOOL DEFINITIONS
// ============================================================================

const tools = [
  {
    name: 'create_invoice',
    description: 'Create a customer invoice (account.move) in Odoo',
    inputSchema: {
      type: 'object',
      properties: {
        contact_name: {
          type: 'string',
          description: 'Customer/Partner name (will search or create if not found)'
        },
        amount: {
          type: 'number',
          description: 'Invoice amount (total)'
        },
        description: {
          type: 'string',
          description: 'Invoice line description/memo'
        },
        due_date: {
          type: 'string',
          description: 'Due date in YYYY-MM-DD format (optional, defaults to 30 days from now)'
        },
        invoice_line_items: {
          type: 'array',
          description: 'Optional detailed line items (name, quantity, price_unit)',
          items: {
            type: 'object',
            properties: {
              name: { type: 'string' },
              quantity: { type: 'number' },
              price_unit: { type: 'number' }
            }
          }
        }
      },
      required: ['contact_name', 'amount', 'description']
    }
  },
  {
    name: 'create_bill',
    description: 'Create a vendor bill (account.move type=in_invoice) in Odoo',
    inputSchema: {
      type: 'object',
      properties: {
        vendor_name: {
          type: 'string',
          description: 'Vendor/Supplier name'
        },
        amount: {
          type: 'number',
          description: 'Bill total amount'
        },
        description: {
          type: 'string',
          description: 'Bill line description/memo'
        },
        due_date: {
          type: 'string',
          description: 'Due date in YYYY-MM-DD format (optional)'
        }
      },
      required: ['vendor_name', 'amount', 'description']
    }
  },
  {
    name: 'log_transaction',
    description: 'Log a journal entry (account.move) for bank/accounting transactions',
    inputSchema: {
      type: 'object',
      properties: {
        amount: { type: 'number', description: 'Transaction amount' },
        description: { type: 'string', description: 'Transaction description' },
        account: { type: 'string', description: 'Account code or name' },
        transaction_type: { type: 'string', description: 'BANK, EXPENSE, REVENUE, etc.' },
        date: { type: 'string', description: 'Transaction date in YYYY-MM-DD format' },
        bank_account_code: { type: 'string', description: 'Bank account code (optional)' }
      },
      required: ['amount', 'description', 'account', 'transaction_type']
    }
  },
  {
    name: 'get_accounts',
    description: 'Fetch list of accounts (chart of accounts) from Odoo',
    inputSchema: {
      type: 'object',
      properties: {
        filter_type: {
          type: 'string',
          description: 'Filter by type: asset, liability, equity, revenue, expense, bank, payable, receivable (optional)'
        },
        limit: {
          type: 'number',
          description: 'Max number of accounts to return (default: 100)'
        }
      }
    }
  },
  {
    name: 'get_invoices',
    description: 'Query invoices from Odoo with filters',
    inputSchema: {
      type: 'object',
      properties: {
        status: {
          type: 'string',
          description: 'Filter by status: draft, posted, paid, cancelled (optional)'
        },
        customer_name: {
          type: 'string',
          description: 'Filter by customer name (optional, partial match)'
        },
        from_date: {
          type: 'string',
          description: 'From date in YYYY-MM-DD format (optional)'
        },
        to_date: {
          type: 'string',
          description: 'To date in YYYY-MM-DD format (optional)'
        },
        limit: {
          type: 'number',
          description: 'Max number of invoices to return (default: 50)'
        }
      }
    }
  },
  {
    name: 'get_balance',
    description: 'Get account balance or balance sheet data',
    inputSchema: {
      type: 'object',
      properties: {
        account_code: {
          type: 'string',
          description: 'Account code to get balance for (optional)'
        },
        as_of_date: {
          type: 'string',
          description: 'Balance as of date in YYYY-MM-DD format (default: today)'
        }
      }
    }
  },
  {
    name: 'get_profit_loss',
    description: 'Generate profit & loss report for a date range',
    inputSchema: {
      type: 'object',
      properties: {
        from_date: {
          type: 'string',
          description: 'Start date in YYYY-MM-DD format (required)'
        },
        to_date: {
          type: 'string',
          description: 'End date in YYYY-MM-DD format (required)'
        }
      },
      required: ['from_date', 'to_date']
    }
  }
];

// ============================================================================
// ODOO JSON-RPC CLIENT
// ============================================================================

async function call(service, method, args, kwargs = {}) {
  try {
    const response = await axios.post(ENDPOINT, {
      jsonrpc: '2.0',
      method: 'call',
      params: {
        service,
        method,
        args,
        kwargs
      },
      id: Math.random().toString(36).substr(2, 9)
    });

    if (response.data.error) {
      throw new Error(`Odoo error: ${response.data.error.message}`);
    }

    return response.data.result;
  } catch (error) {
    throw new Error(`Odoo RPC call failed: ${error.message}`);
  }
}

async function authenticate() {
  try {
    if (sessionId && userId) return;

    // Odoo authentication via JSON-RPC
    const result = await call('common', 'login', [ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD]);

    if (!result) {
      throw new Error('Authentication failed: invalid credentials');
    }

    userId = result;
    console.error(`✓ Odoo authenticated as user ${userId}`);
  } catch (error) {
    console.error(`✗ Authentication error: ${error.message}`);
    throw error;
  }
}

// ============================================================================
// TOOL IMPLEMENTATIONS
// ============================================================================

async function createInvoice(input) {
  await authenticate();

  try {
    const { contact_name, amount, description, due_date, invoice_line_items } = input;

    // Find or create partner
    let partnerId;
    const partners = await call('object', 'execute_kw', [
      ODOO_DB, userId, ODOO_PASSWORD, 'res.partner', 'search',
      [[['name', '=', contact_name]]], { limit: 1 }
    ]);

    if (partners.length > 0) {
      partnerId = partners[0];
    } else {
      // Create new partner
      partnerId = await call('object', 'execute_kw', [
        ODOO_DB, userId, ODOO_PASSWORD, 'res.partner', 'create',
        [{ name: contact_name, is_company: true }]
      ]);
    }

    // Prepare invoice lines
    const invoiceLines = [];
    if (invoice_line_items && invoice_line_items.length > 0) {
      for (const item of invoice_line_items) {
        invoiceLines.push([0, 0, {
          name: item.name,
          quantity: item.quantity || 1,
          price_unit: item.price_unit || (amount / invoice_line_items.length)
        }]);
      }
    } else {
      // Single line item
      invoiceLines.push([0, 0, {
        name: description,
        quantity: 1,
        price_unit: amount
      }]);
    }

    // Create invoice
    const invoiceData = {
      move_type: 'out_invoice',
      partner_id: partnerId,
      invoice_line_ids: invoiceLines,
      invoice_date: new Date().toISOString().split('T')[0],
      invoice_date_due: due_date || new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      state: 'draft'
    };

    const invoiceId = await call('object', 'execute_kw', [
      ODOO_DB, userId, ODOO_PASSWORD, 'account.move', 'create',
      [invoiceData]
    ]);

    return {
      status: 'created',
      invoice_id: invoiceId,
      partner_id: partnerId,
      amount: amount,
      message: `Invoice ${invoiceId} created for ${contact_name}`
    };
  } catch (error) {
    return {
      status: 'error',
      error: 'Failed to create invoice',
      detail: error.message
    };
  }
}

async function createBill(input) {
  await authenticate();

  try {
    const { vendor_name, amount, description, due_date } = input;

    // Find or create vendor partner
    let partnerId;
    const partners = await call('object', 'execute_kw', [
      ODOO_DB, userId, ODOO_PASSWORD, 'res.partner', 'search',
      [[['name', '=', vendor_name]]], { limit: 1 }
    ]);

    if (partners.length > 0) {
      partnerId = partners[0];
    } else {
      partnerId = await call('object', 'execute_kw', [
        ODOO_DB, userId, ODOO_PASSWORD, 'res.partner', 'create',
        [{ name: vendor_name, is_company: true, supplier_rank: 1 }]
      ]);
    }

    // Create bill
    const billData = {
      move_type: 'in_invoice',
      partner_id: partnerId,
      invoice_line_ids: [[0, 0, {
        name: description,
        quantity: 1,
        price_unit: amount
      }]],
      invoice_date: new Date().toISOString().split('T')[0],
      invoice_date_due: due_date || new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      state: 'draft'
    };

    const billId = await call('object', 'execute_kw', [
      ODOO_DB, userId, ODOO_PASSWORD, 'account.move', 'create',
      [billData]
    ]);

    return {
      status: 'created',
      bill_id: billId,
      vendor_id: partnerId,
      amount: amount,
      message: `Bill ${billId} created for ${vendor_name}`
    };
  } catch (error) {
    return {
      status: 'error',
      error: 'Failed to create bill',
      detail: error.message
    };
  }
}

async function logTransaction(input) {
  await authenticate();

  try {
    const { amount, description, account, transaction_type, date, bank_account_code } = input;

    // Map transaction type to account type
    const accountType = {
      'BANK': 'asset',
      'EXPENSE': 'expense',
      'REVENUE': 'revenue',
      'PAYABLE': 'liability',
      'RECEIVABLE': 'asset'
    }[transaction_type] || 'other';

    // Create journal entry
    const entryData = {
      move_type: 'entry',
      journal_id: 1, // General journal (ID=1 in most Odoo instances)
      line_ids: [[0, 0, {
        name: description,
        account_id: 1, // Placeholder - should search actual account
        debit: amount > 0 ? amount : 0,
        credit: amount < 0 ? Math.abs(amount) : 0
      }]],
      date: date || new Date().toISOString().split('T')[0],
      state: 'draft'
    };

    const entryId = await call('object', 'execute_kw', [
      ODOO_DB, userId, ODOO_PASSWORD, 'account.move', 'create',
      [entryData]
    ]);

    return {
      status: 'logged',
      transaction_id: entryId,
      amount: amount,
      account: account,
      message: `Transaction ${entryId} logged for ${description}`
    };
  } catch (error) {
    return {
      status: 'error',
      error: 'Failed to log transaction',
      detail: error.message
    };
  }
}

async function getAccounts(input) {
  await authenticate();

  try {
    const { filter_type, limit = 100 } = input;

    let domain = [];
    if (filter_type) {
      domain = [[['internal_type', '=', filter_type]]];
    }

    const accounts = await call('object', 'execute_kw', [
      ODOO_DB, userId, ODOO_PASSWORD, 'account.account', 'search_read',
      [domain, ['id', 'code', 'name', 'internal_type', 'current_balance']], { limit }
    ]);

    return {
      status: 'success',
      accounts: accounts,
      count: accounts.length
    };
  } catch (error) {
    return {
      status: 'error',
      error: 'Failed to fetch accounts',
      detail: error.message
    };
  }
}

async function getInvoices(input) {
  await authenticate();

  try {
    const { status, customer_name, from_date, to_date, limit = 50 } = input;

    let domain = [['move_type', '=', 'out_invoice']];

    if (status) {
      domain.push(['state', '=', status]);
    }
    if (customer_name) {
      domain.push(['partner_id.name', 'ilike', customer_name]);
    }
    if (from_date) {
      domain.push(['invoice_date', '>=', from_date]);
    }
    if (to_date) {
      domain.push(['invoice_date', '<=', to_date]);
    }

    const invoices = await call('object', 'execute_kw', [
      ODOO_DB, userId, ODOO_PASSWORD, 'account.move', 'search_read',
      [domain, ['id', 'name', 'partner_id', 'invoice_date', 'amount_total', 'state']], { limit }
    ]);

    return {
      status: 'success',
      invoices: invoices,
      count: invoices.length
    };
  } catch (error) {
    return {
      status: 'error',
      error: 'Failed to fetch invoices',
      detail: error.message
    };
  }
}

async function getBalance(input) {
  await authenticate();

  try {
    const { account_code, as_of_date } = input;

    let domain = [];
    if (account_code) {
      domain = [[['code', '=', account_code]]];
    }

    const accounts = await call('object', 'execute_kw', [
      ODOO_DB, userId, ODOO_PASSWORD, 'account.account', 'search_read',
      [domain, ['id', 'code', 'name', 'current_balance']], { limit: 1 }
    ]);

    return {
      status: 'success',
      accounts: accounts,
      as_of_date: as_of_date || new Date().toISOString().split('T')[0]
    };
  } catch (error) {
    return {
      status: 'error',
      error: 'Failed to fetch balance',
      detail: error.message
    };
  }
}

async function getProfitLoss(input) {
  await authenticate();

  try {
    const { from_date, to_date } = input;

    // Fetch P&L report data
    const domain = [
      ['move_id.move_type', '!=', 'entry'],
      ['move_id.state', '=', 'posted'],
      ['move_id.date', '>=', from_date],
      ['move_id.date', '<=', to_date]
    ];

    const lines = await call('object', 'execute_kw', [
      ODOO_DB, userId, ODOO_PASSWORD, 'account.move.line', 'search_read',
      [domain, ['account_id', 'debit', 'credit']], { limit: 1000 }
    ]);

    // Calculate totals
    let totalRevenue = 0, totalExpenses = 0;
    for (const line of lines) {
      totalRevenue += line.debit || 0;
      totalExpenses += line.credit || 0;
    }

    const netProfit = totalRevenue - totalExpenses;

    return {
      status: 'success',
      period: { from: from_date, to: to_date },
      revenue: totalRevenue,
      expenses: totalExpenses,
      net_profit: netProfit,
      line_count: lines.length
    };
  } catch (error) {
    return {
      status: 'error',
      error: 'Failed to generate P&L report',
      detail: error.message
    };
  }
}

// ============================================================================
// TOOL DISPATCHER
// ============================================================================

async function processTool(toolName, input) {
  switch (toolName) {
    case 'create_invoice':
      return await createInvoice(input);
    case 'create_bill':
      return await createBill(input);
    case 'log_transaction':
      return await logTransaction(input);
    case 'get_accounts':
      return await getAccounts(input);
    case 'get_invoices':
      return await getInvoices(input);
    case 'get_balance':
      return await getBalance(input);
    case 'get_profit_loss':
      return await getProfitLoss(input);
    default:
      return {
        status: 'error',
        error: `Unknown tool: ${toolName}`
      };
  }
}

// ============================================================================
// LEGACY STDIO TRANSPORT (For backward compatibility with orchestrator.py)
// ============================================================================

async function handleStdioRequest(line) {
  try {
    const request = JSON.parse(line);
    const { tool, input } = request;

    const result = await processTool(tool, input);
    console.log(JSON.stringify(result));
  } catch (error) {
    console.log(JSON.stringify({
      status: 'error',
      error: error.message
    }));
  }
}

// ============================================================================
// MAIN
// ============================================================================

// Check for --legacy-stdio flag (used by orchestrator.py)
const legacyStdio = process.argv.includes('--legacy-stdio');

if (legacyStdio) {
  // Read from stdin line-by-line
  const readline = require('readline');
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: false
  });

  rl.on('line', async (line) => {
    if (line.trim()) {
      await handleStdioRequest(line);
    }
  });

  rl.on('close', () => {
    process.exit(0);
  });
} else {
  // Print available tools and exit (for testing/documentation)
  console.error('Odoo MCP Server');
  console.error('Available tools:');
  tools.forEach(tool => {
    console.error(`  - ${tool.name}: ${tool.description}`);
  });
  console.error('\nUsage: node index.js --legacy-stdio');
  process.exit(0);
}
