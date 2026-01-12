#!/usr/bin/env node

/**
 * Xero MCP Server - Real Xero API Integration
 * Uses xero-python SDK via Python subprocess
 */

const axios = require('axios');

const XERO_API_BASE = 'https://api.xero.com/api.xro/2.0';

const tools = [
  {
    name: 'create_invoice',
    description: 'Create a new invoice in Xero',
    inputSchema: {
      type: 'object',
      properties: {
        contact_id: { type: 'string', description: 'Xero contact ID' },
        contact_name: { type: 'string', description: 'Contact name if not using ID' },
        invoice_number: { type: 'string', description: 'Invoice number' },
        amount: { type: 'number', description: 'Total invoice amount' },
        description: { type: 'string', description: 'Invoice line description' },
        due_date: { type: 'string', description: 'Due date (YYYY-MM-DD)' }
      },
      required: ['contact_name', 'amount', 'description']
    }
  },
  {
    name: 'log_transaction',
    description: 'Log transaction to Xero accounting system',
    inputSchema: {
      type: 'object',
      properties: {
        amount: { type: 'number', description: 'Transaction amount' },
        description: { type: 'string', description: 'Transaction description' },
        account: { type: 'string', description: 'Account code' },
        transaction_type: { type: 'string', enum: ['RECEIVE', 'SPEND', 'ACCRECPAYABLE', 'ACCRECEIVABLE', 'BANK', 'EXPENSE'], description: 'Transaction type' },
        bank_account_code: { type: 'string', description: 'Bank account code for BankTransactions' },
        date: { type: 'string', description: 'Transaction date (YYYY-MM-DD)' }
      },
      required: ['amount', 'description', 'account']
    }
  },
  {
    name: 'get_balance',
    description: 'Get current account balance and financial summary',
    inputSchema: {
      type: 'object',
      properties: {
        account_code: { type: 'string', description: 'Specific account code (optional)' },
        period: { type: 'string', enum: ['current_month', 'current_year', 'all_time'], description: 'Period for balance', default: 'current_month' }
      }
    }
  },
  {
    name: 'get_invoices',
    description: 'Retrieve invoices with optional filtering',
    inputSchema: {
      type: 'object',
      properties: {
        status: { type: 'string', enum: ['DRAFT', 'SUBMITTED', 'AUTHORISED', 'PAID'], description: 'Invoice status filter' },
        limit: { type: 'number', description: 'Max results', default: 20 }
      }
    }
  },
  {
    name: 'get_profit_loss',
    description: 'Generate profit & loss statement',
    inputSchema: {
      type: 'object',
      properties: {
        from_date: { type: 'string', description: 'Start date (YYYY-MM-DD)' },
        to_date: { type: 'string', description: 'End date (YYYY-MM-DD)' }
      }
    }
  }
];

/**
 * Get access token from environment
 */
function getAccessToken() {
  const token = process.env.XERO_ACCESS_TOKEN;
  if (!token) {
    console.error('Warning: XERO_ACCESS_TOKEN not configured');
  }
  return token;
}

function getTenantId() {
  const tenantId = process.env.XERO_TENANT_ID;
  if (!tenantId) {
    console.error('Warning: XERO_TENANT_ID not configured');
  }
  return tenantId;
}

function buildHeaders(token, tenantId) {
  return {
    Authorization: `Bearer ${token}`,
    'Xero-Tenant-Id': tenantId,
    Accept: 'application/json'
  };
}

/**
 * Process Xero MCP tools - Real API calls
 */
async function processTool(name, args) {
  const token = getAccessToken();
  const tenantId = getTenantId();
  const timestamp = new Date().toISOString();

  if (!token || !tenantId) {
    return { error: 'Xero credentials not configured. Set XERO_ACCESS_TOKEN and XERO_TENANT_ID in .env' };
  }

  try {
    switch(name) {
      case 'create_invoice': {
        const invoiceId = `INV-${Date.now().toString().slice(-6)}`;

        // Construct invoice for Xero API
        const payload = {
          Type: 'ACCREC',
          Status: 'DRAFT',
          LineItems: [{
            Description: args.description,
            Quantity: 1,
            UnitAmount: args.amount,
            AccountCode: '200'
          }],
          Contact: {
            Name: args.contact_name
          },
          InvoiceNumber: args.invoice_number || invoiceId,
          DueDate: args.due_date || new Date(Date.now() + 30*24*60*60*1000).toISOString().split('T')[0]
        };

        try {
          const response = await axios.post(
            `${XERO_API_BASE}/Invoices`,
            payload,
            { headers: buildHeaders(token, tenantId) }
          );

          return {
            status: 'created',
            invoice_id: response.data.Invoices?.[0]?.InvoiceID || invoiceId,
            invoice_number: args.invoice_number || invoiceId,
            contact: args.contact_name,
            amount: args.amount,
            created_at: timestamp
          };
        } catch (e) {
          console.error('Xero API error:', e.message);
          return { error: 'Xero invoice creation failed', detail: e.message };
        }
      }

      case 'log_transaction': {
        const txnId = `TXN-${Date.now().toString().slice(-6)}`;
        const bankAccountCode = args.bank_account_code || process.env.XERO_BANK_ACCOUNT_CODE;
        if (!bankAccountCode) {
          return { error: 'Missing bank account code. Set bank_account_code or XERO_BANK_ACCOUNT_CODE.' };
        }
        const typeMap = {
          ACCRECPAYABLE: 'SPEND',
          ACCRECEIVABLE: 'RECEIVE',
          BANK: 'RECEIVE',
          EXPENSE: 'SPEND'
        };
        const transactionType = typeMap[args.transaction_type] || args.transaction_type || 'RECEIVE';

        // Construct bank transaction for Xero
        const payload = {
          Type: transactionType,
          Status: 'AUTHORISED',
          LineItems: [{
            Description: args.description,
            Quantity: 1,
            UnitAmount: args.amount,
            AccountCode: args.account || '200'
          }],
          Contact: { Name: 'Internal' },
          BankAccount: { Code: bankAccountCode },
          Date: args.date || new Date().toISOString().split('T')[0]
        };

        try {
          await axios.post(
            `${XERO_API_BASE}/BankTransactions`,
            payload,
            { headers: buildHeaders(token, tenantId) }
          );
        } catch (e) {
          console.error('Xero transaction API error:', e.message);
          return { error: 'Xero transaction logging failed', detail: e.message };
        }

        return {
          status: 'logged',
          transaction_id: txnId,
          amount: args.amount,
          description: args.description,
          account: args.account,
          transaction_type: args.transaction_type || 'BANK',
          date: args.date || new Date().toISOString().split('T')[0],
          timestamp: timestamp
        };
      }

      case 'get_balance': {
        try {
          const response = await axios.get(
            `${XERO_API_BASE}/Reports/BalanceSheet`,
            { headers: buildHeaders(token, tenantId) }
          );

          return {
            period: args.period || 'current_month',
            report: response.data.Reports?.[0] || response.data,
            updated_at: timestamp
          };
        } catch (e) {
          console.error('Xero balance API error:', e.message);
          return {
            period: args.period || 'current_month',
            error: 'Could not fetch balance from Xero'
          };
        }
      }

      case 'get_invoices': {
        try {
          const query = args.status ? `Status="${args.status}"` : '';
          const response = await axios.get(
            `${XERO_API_BASE}/Invoices${query ? `?where=${query}` : ''}`,
            { headers: buildHeaders(token, tenantId) }
          );

          const invoices = (response.data.Invoices || []).slice(0, args.limit || 20).map(inv => ({
            id: inv.InvoiceID,
            number: inv.InvoiceNumber,
            contact: inv.Contact?.Name,
            amount: inv.Total,
            status: inv.Status,
            due_date: inv.DueDate
          }));

          return {
            invoices,
            count: invoices.length,
            limit: args.limit || 20
          };
        } catch (e) {
          console.error('Xero invoices API error:', e.message);
          return { invoices: [], count: 0, error: 'Could not fetch invoices from Xero' };
        }
      }

      case 'get_profit_loss': {
        try {
          const params = {};
          if (args.from_date) {
            params.fromDate = args.from_date;
          }
          if (args.to_date) {
            params.toDate = args.to_date;
          }
          const response = await axios.get(
            `${XERO_API_BASE}/Reports/ProfitAndLoss`,
            { headers: buildHeaders(token, tenantId), params }
          );

          return {
            from_date: args.from_date,
            to_date: args.to_date,
            report: response.data.Reports?.[0] || response.data,
            statement_date: timestamp
          };
        } catch (e) {
          console.error('Xero P&L API error:', e.message);
          return {
            error: 'Could not fetch P&L report from Xero',
            from_date: args.from_date,
            to_date: args.to_date
          };
        }
      }

      default:
        return { error: `Unknown tool: ${name}` };
    }
  } catch (error) {
    console.error(`Xero MCP error for ${name}:`, error.message);
    return { error: `Tool execution failed: ${error.message}` };
  }
}

function startLegacyServer() {
  console.error('Xero MCP (legacy stdio) starting...');
  let inputBuffer = '';

  async function handleRequest(raw) {
    const request = JSON.parse(raw);
    const result = await processTool(request.tool, request.input || {});
    process.stdout.write(JSON.stringify(result));
  }

  process.stdin.on('data', async (chunk) => {
    inputBuffer += chunk.toString();
    while (inputBuffer.includes('\n')) {
      const idx = inputBuffer.indexOf('\n');
      const line = inputBuffer.slice(0, idx).trim();
      inputBuffer = inputBuffer.slice(idx + 1);
      if (!line) {
        continue;
      }
      try {
        await handleRequest(line);
      } catch (error) {
        // Wait for complete JSON
        inputBuffer = line + '\n' + inputBuffer;
        break;
      }
    }
  });

  process.stdin.on('end', async () => {
    const remaining = inputBuffer.trim();
    if (!remaining) {
      process.exit(0);
      return;
    }
    try {
      await handleRequest(remaining);
      process.exit(0);
    } catch (error) {
      console.error(`Invalid MCP request: ${error.message}`);
      process.exit(1);
    }
  });
}

if (process.argv.includes('--legacy-stdio')) {
  startLegacyServer();
} else {
  startLegacyServer();
}
