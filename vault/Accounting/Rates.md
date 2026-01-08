# Billing Rates & Invoice Templates

**Last Updated**: 2026-01-08
**Currency**: USD

---

## Service Rates

### Hourly Rates

| Service | Hourly Rate | Description |
|---------|-------------|-------------|
| Consulting | $100 | General business consulting |
| Development | $150 | Software development |
| Design | $120 | UI/UX design work |
| Support | $50 | Technical support (reduced rate) |

---

### Project Rates

| Project Type | Fixed Price | Duration | Notes |
|--------------|-------------|----------|-------|
| Small Project | $1,000 | 1-2 weeks | Limited scope |
| Medium Project | $3,000 | 2-4 weeks | Standard scope |
| Large Project | $5,000+ | 4+ weeks | Custom quote |

---

## Invoice Settings

### Payment Terms
- Standard: Net 30 (due within 30 days)
- Rush: Net 15 (due within 15 days)
- Deposit: 50% upfront for new clients

### Accepted Payment Methods
- Bank Transfer
- Credit Card (add 3% fee)
- PayPal (add 2.9% + $0.30 fee)

### Late Payment
- Grace period: 5 days
- Late fee: 1.5% per month
- Collections email: Auto-send after 45 days

---

## Client Invoice Mapping

| Client | Hourly Rate | Default Terms |
|--------|-------------|---------------|
| [Client Name 1] | $100 | Net 30 |
| [Client Name 2] | $120 | Net 15 |

---

## Invoice Template

```
# INVOICE

**Invoice #**: [Auto-generated]
**Date**: [Today]
**Due Date**: [Today + 30 days]
**Client**: [Client Name]

## Services Rendered

| Description | Hours | Rate | Amount |
|-------------|-------|------|--------|
| [Service] | [Hours] | $100 | $X,XXX |

**Subtotal**: $X,XXX
**Tax (0%)**: $0
**Total Due**: $X,XXX

**Payment Instructions**: [Add Xero payment link]
```

---

## Notes

Update rates quarterly. AI Employee will use these rates for auto-generating invoices.
