# Odoo MCP Server

This is a Model Context Protocol (MCP) server that integrates with Odoo Community Edition via its JSON-RPC API.

## Overview

The Odoo MCP server provides accounting and ERP operations through standardized MCP tools:

- **create_invoice**: Create customer invoices
- **create_bill**: Create vendor bills
- **log_transaction**: Record journal entries for bank transactions
- **get_accounts**: Fetch chart of accounts
- **get_invoices**: Query invoices with filters
- **get_balance**: Get account balances
- **get_profit_loss**: Generate P&L reports

## Architecture

```
┌─────────────────────────────────────────┐
│  orchestrator.py (Local/Cloud Agent)    │
│                                         │
│  Needs transaction? → Call MCP          │
└────────────────────┬────────────────────┘
                     │
                     │ stdio JSON
                     │
        ┌────────────▼──────────────┐
        │  Odoo MCP Server (Node.js)│
        │                           │
        │  • Authenticate to Odoo   │
        │  • Parse requests         │
        │  • Call JSON-RPC API      │
        │  • Return results         │
        └────────────────┬──────────┘
                         │
                         │ HTTP POST
                         │
        ┌────────────────▼──────────────┐
        │   Odoo 19 Community            │
        │   (Docker container)           │
        │   http://localhost:8069        │
        │                                │
        │   /jsonrpc endpoint            │
        └────────────────────────────────┘
```

## Setup

### Prerequisites

- Node.js >= 14
- Odoo 19 Community Edition (running via Docker Compose)
- Odoo database and admin credentials

### Installation

```bash
cd mcp_servers/odoo_mcp
npm install
```

### Environment Variables

Create a `.env` file or set these in your system environment:

```env
ODOO_URL=http://localhost:8069
ODOO_DB=gte
ODOO_USERNAME=admin
ODOO_PASSWORD=your_odoo_password
```

### Running the Server

```bash
# Legacy stdio mode (used by orchestrator.py)
node index.js --legacy-stdio

# Or via npm
npm start -- --legacy-stdio
```

## JSON-RPC API Integration

The server communicates with Odoo via its standard JSON-RPC API:

**Endpoint**: `http://localhost:8069/jsonrpc`

**Authentication Flow**:

```json
POST /jsonrpc
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "service": "common",
    "method": "login",
    "args": ["database", "username", "password"]
  },
  "id": "unique_id"
}
```

**Response**:

```json
{
  "jsonrpc": "2.0",
  "result": 2,
  "id": "unique_id"
}
```

## Usage Examples

### Create Invoice

**Request** (from orchestrator.py):

```json
{
  "tool": "create_invoice",
  "input": {
    "contact_name": "Acme Corp",
    "amount": 1500.00,
    "description": "Web Development Services",
    "due_date": "2026-02-18"
  }
}
```

**Response**:

```json
{
  "status": "created",
  "invoice_id": 42,
  "partner_id": 15,
  "amount": 1500,
  "message": "Invoice 42 created for Acme Corp"
}
```

### Log Transaction

**Request**:

```json
{
  "tool": "log_transaction",
  "input": {
    "amount": 500.00,
    "description": "Payment received from customer",
    "account": "1010",
    "transaction_type": "BANK",
    "date": "2026-01-18"
  }
}
```

**Response**:

```json
{
  "status": "logged",
  "transaction_id": 1023,
  "amount": 500,
  "account": "1010",
  "message": "Transaction 1023 logged for Payment received from customer"
}
```

### Get Invoices

**Request**:

```json
{
  "tool": "get_invoices",
  "input": {
    "status": "posted",
    "from_date": "2026-01-01",
    "to_date": "2026-01-31",
    "limit": 50
  }
}
```

**Response**:

```json
{
  "status": "success",
  "invoices": [
    {
      "id": 42,
      "name": "INV/2026/0001",
      "partner_id": [15, "Acme Corp"],
      "invoice_date": "2026-01-15",
      "amount_total": 1500.0,
      "state": "posted"
    }
  ],
  "count": 1
}
```

## Odoo Module Requirements

For full functionality, ensure these modules are installed in your Odoo instance:

- `account`: Core accounting module
- `sale`: Sales/invoicing
- `purchase`: Purchasing/bills
- `base`: Base Odoo functionality

Install modules via Odoo UI: **Apps → Search → Install**

## Docker Compose Integration

The Odoo server is deployed via Docker Compose:

```bash
# Start Odoo
docker-compose up -d

# Stop Odoo
docker-compose down

# View logs
docker-compose logs -f odoo

# Shell access to Odoo container
docker-compose exec odoo bash
```

## Odoo Initial Setup

When Odoo starts for the first time:

1. Access http://localhost:8069
2. Create database `gte` with password set to `ODOO_PASSWORD` from .env
3. Install demo data (optional)
4. Create admin user or use default `admin:admin`

**Recommended**: Set admin password in `ODOO_PASSWORD` env var

## Security Considerations

- **Never commit credentials** to git (use .env.example as template)
- **Use strong passwords** in production (change default `admin` password)
- **Firewall Odoo ports**: Only expose 8069 behind HTTPS reverse proxy
- **Rotate credentials** monthly and update .env

## Troubleshooting

### "Authentication failed: invalid credentials"

```bash
# Verify Odoo is running
docker-compose ps odoo

# Check credentials match database
docker-compose logs odoo | grep -i login
```

### "Connection refused to localhost:8069"

```bash
# Ensure docker-compose is running
docker-compose up -d

# Wait for health check to pass
docker-compose exec postgres psql -U odoo -d gte -c "SELECT 1"
```

### "Journal not found"

The MCP server defaults to journal ID=1 (General Journal). Verify it exists:

- Access Odoo: Accounting → Configuration → Journals
- Note the journal ID and update in `logTransaction()`

## Odoo Database Access

To directly query the database:

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U odoo -d gte

# List invoices
SELECT id, name, amount_total, state FROM account_move
WHERE move_type = 'out_invoice' ORDER BY create_date DESC LIMIT 5;

# List partners
SELECT id, name FROM res_partner ORDER BY create_date DESC LIMIT 10;
```

## Integration with Orchestrator

The orchestrator (`agents/orchestrator.py`) calls Odoo MCP when processing:

- **Invoices**: `_execute_invoice()` → `_call_odoo_mcp_create_invoice()`
- **Payments**: `_execute_payment()` → `_call_odoo_mcp_log_transaction()`
- **CEO Briefing**: Fetches financial data via Odoo API (in progress)

## License

MIT
