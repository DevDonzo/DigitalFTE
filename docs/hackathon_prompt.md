# Hackathon Judge Prompt - DigitalFTE

You are evaluating "DigitalFTE", a local-first Personal AI Employee that turns an Obsidian vault into a working business assistant. The system connects watchers (Gmail + WhatsApp via Twilio) to a Claude-driven orchestrator and MCP servers for external actions, with human-in-the-loop approvals for sensitive steps.

## What to Evaluate

- Local-first architecture (vault-backed memory and logs).
- Autonomy with safety (HITL approval gates).
- Multi-domain coverage (personal + business).
- Real integrations (Gmail, Xero, Meta Social, Twitter) when credentials are provided.

## Suggested Demo Flow (5-8 minutes)

1) Show vault structure and Dashboard.
2) Trigger an email watcher entry -> create a draft in Pending_Approval.
3) Send a WhatsApp message through Twilio webhook -> Needs_Action -> draft -> approval.
4) Approve a social post -> Meta or Twitter MCP.
5) Run weekly audit -> CEO briefing output.

## Notes for Judges

- Browser MCP is a placeholder (no Playwright automation).
- Xero/Meta/Twitter actions require valid credentials and vendor approvals.
- All AI actions are routed through Agent Skills for reproducibility.
