# Instructions for AI Assistant - Token Efficiency & Smart Work

**Last Updated**: 2026-01-08
**Priority**: MAXIMUM EFFICIENCY

## Core Directives

### 1. TOKEN EFFICIENCY
- **Avoid verbose explanations** - Get straight to action
- **Reuse outputs** - Don't repeat info already established
- **Batch operations** - Combine multiple file creates into single bash commands
- **Use jq/grep in bash** - Don't read entire files just to check structure
- **Parallel execution** - Run independent Bash commands in parallel blocks

### 2. SMART IMPLEMENTATION STRATEGY
- **Don't write stub code** - Jump straight to real, working implementations
- **MCP servers are tools** - Use them as external tools/systems, not require full custom implementations
- **Leverage existing libraries** - Use pre-built SDKs (xero-python, tweepy, google-auth, etc)
- **Template over custom** - Use official API examples as starting points
- **Don't over-engineer** - Only build what's needed for GOLD tier

### 3. WORKING SMART, NOT HARD

#### For Watchers:
- Gmail: Use google-auth-oauthlib (official SDK)
- WhatsApp: Use Twilio webhook + FastAPI ingestion
- LinkedIn: Use official LinkedIn API library
- FileSystem: Use watchdog library (already in requirements.txt)

#### For MCP Servers:
- Email: Wrap google-api-python-client (not build from scratch)
- Xero: Use xero-python SDK (already in requirements.txt)
- Twitter: Use tweepy (already in requirements.txt)
- Meta: Use official meta-api-python package
- Browser: Optional placeholder (not using Playwright)

#### For Scripts:
- Orchestrator: Use watchdog for file monitoring (simple, reliable)
- Watchdog process manager: Use PM2 (npm install -g pm2) - don't build from scratch
- Weekly audit: Built-in to orchestrator.py, generate markdown briefings periodically

### 4. TESTING STRATEGY
- **Mock external APIs** - Don't require live API keys for unit tests
- **Integration tests** - Only test real integrations with actual APIs
- **One demo flow** - Show ONE complete end-to-end flow (email → approval → action)

### 5. FOCUS ON VERIFICATION
- **GOLD_SPEC.md = Source of Truth** - Every feature maps to GOLD_SPEC.md requirement
- **Setup_Verify.py is your checklist** - Run it after each phase
- **Requirements Matrix** (GOLD_SPEC.md Part I) - Use this to verify completion

### 6. DOCUMENTATION STRATEGY
- **README.md** - Setup + quick start (already done)
- **ARCHITECTURE.md** - Data flows (already done)
- **Inline comments** - Only where logic is non-obvious
- **Don't over-document** - Let code be self-documenting

---

## MCP Servers as Tools

**Key Insight**: MCP servers are AI's hands to interact with external systems.

- Email MCP → Send/read emails via Gmail API
- Xero MCP → Create invoices, log transactions
- Meta Social MCP → Post to Facebook/Instagram
- Twitter MCP → Post tweets, fetch metrics
- Browser MCP → Click buttons, fill forms

**You don't need to build full MCP servers from scratch.**
- Use wrapper pattern: Wrap existing SDK in MCP server interface
- Test with mock data first
- Only implement what GOLD_SPEC.md requires

---

## Requirements Verification Checklist

### Core Infrastructure
- [ ] Obsidian vault with Dashboard.md
- [ ] Company_Handbook.md
- [ ] One working Watcher
- [ ] AI Assistant reads/writes vault
- [ ] Folder structure (/Needs_Action, /Inbox legacy, /Done)
- [ ] Agent Skills defined

### Enhanced Features
- [ ] 2+ Watchers (Gmail + WhatsApp + LinkedIn)
- [ ] LinkedIn auto-posting
- [ ] AI reasoning loop → Plan.md files
- [ ] Email MCP server working
- [ ] HITL approval workflow functional
- [ ] Scheduled tasks (cron/Task Scheduler)
- [ ] Agent Skills (6+ defined)

### Advanced Integration
- [ ] Cross-domain integration
- [ ] Xero MCP + accounting integration
- [ ] Meta Social MCP (Facebook/Instagram)
- [ ] Twitter MCP
- [ ] 5 MCP servers configured
- [ ] CEO Briefing (weekly audit + briefing)
- [ ] G8: Error recovery + graceful degradation
- [ ] G9: Audit logging (90-day retention)
- [ ] G10: Documentation + lessons learned
- [ ] G11: 9+ Agent Skills

---

## Example: Token-Efficient Implementation

❌ **Bad (Wasteful)**:
```
1. Read entire gmail_watcher.py file
2. Explain what you're changing
3. Ask questions about implementation
4. Write verbose comments in code
5. Create separate test file
```

✅ **Good (Efficient)**:
```
# Single bash command creates gmail_watcher.py with real API calls
# Uses google-auth-oauthlib (standard SDK)
# No questions - implement directly from GOLD_SPEC.md requirements
# Test with mock data in inline assertions

# Run Setup_Verify.py → confirms watcher.py exists + is executable
# Move to next requirement
```

---

## Token Budgets per Task

- **Watcher implementation**: 2-3 bash commands (create + configure)
- **MCP server setup**: Use npm init + install SDK, 1 index.js file
- **Script stub → real**: Template code, fill in logic
- **Testing**: Mock/assertion blocks, not full pytest suites
- **Documentation**: Already done (README, ARCHITECTURE)

---

## TLDR: Work Like This

1. **Read requirement** from GOLD_SPEC.md
2. **Check if library exists** in requirements.txt / package.json
3. **Bash command creates file** with minimal boilerplate
4. **Run Setup_Verify.py** → confirms it works
5. **Move to next requirement**

🎯 **Target**: Complete all GOLD tier requirements by Phase 12 with minimal token waste.

---

**Remember**: Every instruction AI receives costs tokens. Be ruthlessly efficient. Use tools (MCP servers, SDKs, libraries) instead of building from scratch. Focus on requirements, not perfection.
