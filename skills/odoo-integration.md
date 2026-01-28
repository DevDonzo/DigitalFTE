# Odoo Integration Skill

**Purpose**: Integrate with Odoo Community Edition for accounting and invoicing

## Capabilities
- Create customer invoices
- Create vendor bills
- Log bank transactions
- Query invoices
- Generate P&L reports

## Usage
The orchestrator calls Odoo MCP server via JSON-RPC API for all accounting operations.

## MCP Server
Location: `mcp_servers/odoo_mcp/index.js`
Tools: create_invoice, create_bill, log_transaction, get_invoices, get_balance, get_profit_loss
