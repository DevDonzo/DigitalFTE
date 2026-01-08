# Deployment Guide

## Local Development

```bash
# 1. Clone repo
git clone https://github.com/DevDonzo/DigitalFTE.git
cd DigitalFTE

# 2. Copy .env.example to .env
cp .env.example .env
# Edit .env with your credentials

# 3. Install dependencies
pip install -r requirements.txt
npm install  # for MCP servers

# 4. Start system
python watchers/gmail_watcher.py &
python watchers/whatsapp_watcher.py &
python watchers/filesystem_watcher.py &
python scripts/orchestrator.py &

# 5. Monitor
tail -f vault/Logs/*.json
```

## Docker Deployment

```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
RUN npm install

CMD ["sh", "-c", "python watchers/gmail_watcher.py & python scripts/orchestrator.py"]
```

## Continuous Deployment

- GitHub Actions validates every push (see .github/workflows/test.yml)
- Tests run automatically
- Manual approval for production

## Production Checklist

- [ ] All credentials in secure vault (not .env)
- [ ] Logs rotated daily
- [ ] Database backups configured
- [ ] Monitoring alerts set up
- [ ] Error reporting configured
- [ ] HTTPS enabled for APIs

