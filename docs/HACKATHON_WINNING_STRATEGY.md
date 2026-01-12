# Hackathon Winning Strategy - Evidence Map

This is a concise mapping between Gold requirements and the files that implement or demonstrate them.

## Gold Requirement Mapping

- Cross-domain integration (personal + business): `scripts/orchestrator.py`
- Watchers (Gmail + WhatsApp): `watchers/gmail_watcher.py`, `scripts/webhook_server.py`, `watchers/whatsapp_watcher.py`
- Human-in-the-loop approvals: `vault/Pending_Approval/`, `scripts/orchestrator.py`
- Email MCP: `mcp_servers/email_mcp/index.js`
- Xero MCP: `mcp_servers/xero_mcp/index.js`, `auth/xero.py`
- Meta Social MCP: `mcp_servers/meta_social_mcp/index.js`
- Twitter MCP: `mcp_servers/twitter_mcp/index.js`
- CEO briefing system: `scripts/weekly_audit.py`, `vault/Briefings/`
- Error recovery: `utils/error_handler.py`, `docs/ERROR_HANDLING.md`
- Audit logging: `utils/audit_logger.py`, `vault/Logs/`
- Agent Skills: `skills/`
- Architecture documentation: `README.md`, `ARCHITECTURE.md`, `docs/ARCHITECTURE.md`
- Lessons learned: `LESSONS_LEARNED.md`

## Known Gaps (Declared)

- Browser MCP is a placeholder (no Playwright automation). See `mcp_servers/browser_mcp/index.js`.
