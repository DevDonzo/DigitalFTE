# Odoo Setup Guide for DigitalFTE

This guide walks through setting up Odoo 19 Community Edition locally using Docker Compose for the DigitalFTE automation system.

## Quick Start (5 minutes)

### 1. Start Odoo with Docker Compose

```bash
cd /Users/hparacha/DigitalFTE

# Start Odoo + PostgreSQL
docker-compose up -d

# Wait for health checks (15-30 seconds)
docker-compose ps

# Should see: odoo_app (healthy), odoo_postgres (healthy)
```

### 2. Access Odoo Web Interface

Open your browser: **http://localhost:8069**

You'll see the database creation screen.

### 3. Create Database

- **Database Name**: `gte`
- **Email**: your.email@example.com
- **Password**: Choose a strong password (or use ODOO_PASSWORD from .env)
- **Phone**: (optional)
- **Company Name**: Your company name
- **Country**: Select your country
- **Load Demonstration Data**: ✓ (Recommended for testing, can remove later)
- **Install language**: English

Click **Create Database**

Wait 2-3 minutes for initial setup.

### 4. Login

**Username**: admin
**Password**: Password set in step 3

You're now in Odoo!

## Environment Configuration

### .env File

Create or update `.env` file in project root:

```env
# Odoo Configuration
ODOO_URL=http://localhost:8069
ODOO_DB=gte
ODOO_USERNAME=admin
ODOO_PASSWORD=your_chosen_password
```

**Security**: Never commit `.env` to git. Use `.env.example` as template.

## Odoo Configuration

### 1. Chart of Accounts Setup

After login, configure your chart of accounts:

**Path**: Accounting → Configuration → Chart of Accounts

**Key Accounts to Set Up**:
- **1010**: Bank Account
- **2000**: Accounts Payable
- **3000**: Customer Advances
- **4000**: Sales Revenue
- **5000**: Cost of Goods Sold
- **6000**: Operating Expenses

### 2. Create Bank Account

**Path**: Accounting → Configuration → Bank Accounts

**Details**:
- Account Name: "Main Bank Account"
- Account Type: "Bank"
- Account Code: "1010"
- Currency: USD (or your currency)

### 3. Create Customers (Partners)

**Path**: Accounting → Customers → Customers

**Example Customer**:
- Name: Acme Corp
- Email: contact@acmecorp.com
- Phone: (optional)
- Address: (optional)

### 4. Configure Email

**Path**: Settings → General Settings → Email Server

**SMTP Settings** (for sending invoices):
- Server: smtp.gmail.com
- Port: 587
- Use TLS: Yes
- Username: your-email@gmail.com
- Password: your-app-password (use Gmail App Passwords if 2FA enabled)

## MCP Server Setup

### 1. Install Dependencies

```bash
cd mcp_servers/odoo_mcp
npm install
```

### 2. Test Connection

```bash
# Start MCP server in legacy stdio mode
node index.js --legacy-stdio

# In another terminal, test with curl (if you install jq):
curl -X POST http://localhost:8069/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
      "service": "common",
      "method": "version",
      "args": []
    },
    "id": "test"
  }'
```

Should return Odoo version info.

### 3. Verify Orchestrator Integration

```bash
# Test that orchestrator can call Odoo MCP
python3 -c "
import subprocess
import json

request = {
    'tool': 'get_accounts',
    'input': {'limit': 5}
}

proc = subprocess.run(
    ['node', 'mcp_servers/odoo_mcp/index.js', '--legacy-stdio'],
    input=json.dumps(request),
    capture_output=True,
    text=True,
    timeout=10
)

print('Response:', proc.stdout)
"
```

## Database Backup & Restore

### Backup Database

```bash
# Backup Odoo database to file
docker-compose exec postgres pg_dump -U odoo gte > odoo_backup_$(date +%Y%m%d).sql

# Backup with gzip compression
docker-compose exec postgres pg_dump -U odoo gte | gzip > odoo_backup_$(date +%Y%m%d).sql.gz
```

### Restore Database

```bash
# Restore from backup
docker-compose exec -T postgres psql -U odoo gte < odoo_backup_20260118.sql

# Or from gzipped backup
zcat odoo_backup_20260118.sql.gz | docker-compose exec -T postgres psql -U odoo gte
```

## Managing Odoo Modules

### Install a Module

**Via UI**:
1. Go to **Apps**
2. Search for module name
3. Click **Install**

**Via Command Line**:
```bash
docker-compose exec odoo odoo-bin -d gte -i account_invoice_extract --stop-after-init
```

### Common Modules for DigitalFTE

| Module | Purpose |
|--------|---------|
| `account` | Core accounting |
| `sale` | Sales/invoicing |
| `purchase` | Purchasing/bills |
| `account_invoice_extract` | AI invoice reading |
| `mail` | Email integration |
| `web_unseen` | Unread message tracking |
| `web_diagram` | Workflow diagrams |

## Docker Operations

### View Logs

```bash
# Odoo logs
docker-compose logs -f odoo

# PostgreSQL logs
docker-compose logs -f postgres

# Last 50 lines
docker-compose logs --tail=50 odoo
```

### Execute Commands

```bash
# Bash shell in Odoo container
docker-compose exec odoo bash

# Run Odoo CLI tools
docker-compose exec odoo odoo-bin --version

# Database check
docker-compose exec postgres psql -U odoo -d gte -c "SELECT version();"
```

### Restart Services

```bash
# Restart Odoo
docker-compose restart odoo

# Restart PostgreSQL (careful - stops Odoo too)
docker-compose restart postgres

# Full restart
docker-compose down && docker-compose up -d
```

### Delete Everything (Clean Slate)

⚠️ **This deletes all data**

```bash
docker-compose down -v

# Then start fresh
docker-compose up -d
```

## Troubleshooting

### Odoo Won't Start

```bash
# Check health
docker-compose ps

# View startup logs
docker-compose logs odoo | tail -50

# Common causes:
# 1. PostgreSQL not ready - wait 30 seconds and retry
# 2. Port 8069 already in use - change in docker-compose.yml
# 3. Invalid credentials - check ODOO_PASSWORD matches
```

### Database Connection Error

```bash
# Verify PostgreSQL is running
docker-compose ps postgres

# Check database exists
docker-compose exec postgres psql -U odoo -l | grep gte

# Recreate if missing
docker-compose down -v && docker-compose up -d
```

### MCP Authentication Failed

```bash
# Check Odoo is accessible
curl http://localhost:8069/web/health

# Verify credentials
docker-compose exec postgres psql -U odoo -d gte -c "SELECT COUNT(*) FROM res_users;"

# Check logs
docker-compose logs odoo | grep -i "admin\|login"
```

### "Port 8069 is already in use"

```bash
# Find process using port
lsof -i :8069

# Kill it
kill -9 <PID>

# Or change port in docker-compose.yml (8069 → 8070)
```

## Production Deployment Considerations

For production (Cloud VM):

1. **Use environment variables** - Never hardcode credentials
2. **Enable HTTPS** - Use reverse proxy (nginx) with Let's Encrypt
3. **Regular backups** - Daily database backups to cloud storage
4. **Resource limits** - Set memory limits in docker-compose.yml
5. **Monitoring** - Enable health checks and alerts
6. **User management** - Create separate Odoo users for different roles
7. **Module security** - Only install trusted modules
8. **Database encryption** - Enable PostgreSQL SSL
9. **Audit logging** - Enable Odoo audit trail for compliance

### Example Production docker-compose.yml

```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_PASSWORD: ${ODOO_DB_PASSWORD}  # Use strong password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always
    deploy:
      resources:
        limits:
          memory: 2G

  odoo:
    image: odoo:19.0
    depends_on:
      - postgres
    ports:
      - "127.0.0.1:8069:8069"  # Only localhost, behind nginx
    volumes:
      - odoo_data:/var/lib/odoo
    restart: always
    deploy:
      resources:
        limits:
          memory: 4G
```

## Next Steps

1. ✅ Odoo is running locally
2. ✅ Accounts and customers configured
3. → Test MCP server connection (run: `node mcp_servers/odoo_mcp/index.js --legacy-stdio`)
4. → Run Platinum demo flow (email → draft → approve → execute)
5. → Deploy to Oracle Cloud VM for production

## Resources

- **Odoo Documentation**: https://www.odoo.com/documentation/19.0
- **Odoo Community Edition**: https://github.com/odoo/odoo
- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **Docker Compose**: https://docs.docker.com/compose/

## Support

For issues:

1. Check logs: `docker-compose logs odoo`
2. Verify connections: `curl http://localhost:8069/web/health`
3. Test MCP: `node mcp_servers/odoo_mcp/index.js --legacy-stdio`
4. Search Odoo forum: https://www.odoo.com/forum
