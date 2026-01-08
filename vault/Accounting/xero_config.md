# Xero Configuration & Setup

**Status**: Pending Setup
**Organization**: [Your Business Name]
**Created**: 2026-01-08

---

## OAuth 2.0 Setup

### Step 1: Register App at Xero Developer Portal
1. Go to https://developer.xero.com/
2. Create new app (select "Web" app type)
3. Get Client ID and Client Secret
4. Set Redirect URI to: http://localhost:8080/callback

### Step 2: Store Credentials
Add to .env file:
```
XERO_CLIENT_ID=your_client_id
XERO_CLIENT_SECRET=your_client_secret
XERO_REDIRECT_URI=http://localhost:8080/callback
XERO_TENANT_ID=your_tenant_id
```

### Step 3: Authenticate
Run the Xero MCP server and complete OAuth flow in browser.

---

## Organization Settings

**Business Name**: [Your Company]
**Tax ID**: [Your Tax ID]
**Currency**: USD
**Financial Year End**: December 31
**Default Invoice Terms**: Net 30

---

## Bank Accounts

| Account | BSB/Routing | Account # | Status |
|---------|-------------|-----------|--------|
| Primary | [Your BSB] | [Your Account] | Pending |

---

## Chart of Accounts

**Income Accounts**:
- 200-01: Service Revenue
- 200-02: Product Sales
- 200-03: Consulting Fees

**Expense Accounts**:
- 600-01: Software Subscriptions
- 600-02: Contractors
- 600-03: Office Supplies

**Balance Sheet**:
- 1000-01: Business Checking
- 1000-02: Savings Account
- 2000-01: Credit Card Payable

---

## Integration Status

- [ ] OAuth credentials stored
- [ ] Test transaction created
- [ ] Invoice template configured
- [ ] Bank sync enabled
- [ ] Weekly audit enabled

---

## Notes

Xero connection status will be updated by weekly audit in CEO Briefing.
