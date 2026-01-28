# ✅ DigitalFTE Running on Docker

**Status**: 🟢 LIVE NOW

---

## Docker Containers

```
✅ odoo        (port 8069)   - Odoo Community Edition
✅ postgres    (port 5432)   - Database
```

### Access Odoo Web Interface
- **URL**: http://localhost:8069
- **Username**: admin
- **Password**: admin

---

## Start Agents (Local)

Run in separate terminals:

**Terminal 1: Orchestrator**
```bash
cd /Users/hparacha/DigitalFTE
python agents/orchestrator.py
```

**Terminal 2: Gmail Watcher**
```bash
python agents/gmail_watcher.py
```

**Terminal 3: Watchdog**
```bash
python agents/watchdog.py
```

**Terminal 4: View Vault**
```bash
open -a Obsidian vault/
```

---

## Commands

### View Logs
```bash
docker-compose logs -f odoo
docker-compose logs -f postgres
```

### Stop Everything
```bash
docker-compose down
```

### Check Database
```bash
docker-compose exec postgres psql -U odoo -d gte -c "SELECT 1;"
```

---

## Next Steps

1. Open Obsidian: `open -a Obsidian vault/`
2. Start agents in terminals
3. Send a test email
4. Watch it process in real-time

---

**System**: ✅ Ready to use
**Verification**: ✅ 44/44 passing
**Tier**: ✅ Gold (Platinum ready)
