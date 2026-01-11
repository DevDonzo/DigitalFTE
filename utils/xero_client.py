"""Xero API Client - Fetch invoices, transactions, and financial data"""
import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN_FILE = os.path.expanduser('~/.xero_token.json')
CLIENT_ID = os.getenv('XERO_CLIENT_ID')


class XeroClient:
    """Client for Xero Accounting API"""

    BASE_URL = 'https://api.xero.com/api.xro/2.0'

    def __init__(self):
        self.tokens = self._load_tokens()
        if self.tokens:
            self.access_token = self.tokens.get('access_token')
            self.tenant_id = self.tokens.get('tenant_id')
            logger.info(f"✅ Xero connected: {self.tokens.get('tenant_name', 'Unknown')}")
        else:
            self.access_token = None
            self.tenant_id = None
            logger.warning("⚠️ Xero not authenticated. Run: python auth/xero.py")

    def _load_tokens(self) -> Optional[dict]:
        """Load saved tokens"""
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE) as f:
                return json.load(f)
        return None

    def _refresh_if_needed(self):
        """Refresh token if expired"""
        if not self.tokens:
            return False

        # Xero tokens expire in 30 minutes, refresh proactively
        # For simplicity, always try to refresh before API calls
        from auth.xero import refresh_token
        new_tokens = refresh_token()
        if new_tokens:
            self.tokens = new_tokens
            self.access_token = new_tokens.get('access_token')
            return True
        return False

    def _headers(self) -> dict:
        """Get API headers"""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Xero-Tenant-Id': self.tenant_id,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def _get(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """Make GET request to Xero API"""
        if not self.access_token or not self.tenant_id:
            logger.error("Xero not authenticated")
            return None

        url = f"{self.BASE_URL}/{endpoint}"
        try:
            response = requests.get(url, headers=self._headers(), params=params)

            if response.status_code == 401:
                # Try refresh
                if self._refresh_if_needed():
                    response = requests.get(url, headers=self._headers(), params=params)

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Xero API error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Xero request failed: {e}")
            return None

    def get_invoices(self, status: str = None, since_date: datetime = None) -> List[dict]:
        """Get invoices from Xero"""
        params = {}
        if status:
            params['where'] = f'Status=="{status}"'
        if since_date:
            date_str = since_date.strftime('%Y-%m-%d')
            params['where'] = f'Date>=DateTime({since_date.year},{since_date.month},{since_date.day})'

        result = self._get('Invoices', params)
        if result:
            return result.get('Invoices', [])
        return []

    def get_paid_invoices(self, since_date: datetime = None) -> List[dict]:
        """Get paid invoices"""
        return self.get_invoices(status='PAID', since_date=since_date)

    def get_unpaid_invoices(self) -> List[dict]:
        """Get unpaid/outstanding invoices"""
        invoices = []
        for status in ['AUTHORISED', 'SUBMITTED']:
            invoices.extend(self.get_invoices(status=status))
        return invoices

    def get_bank_transactions(self, since_date: datetime = None) -> List[dict]:
        """Get bank transactions"""
        params = {}
        if since_date:
            params['where'] = f'Date>=DateTime({since_date.year},{since_date.month},{since_date.day})'

        result = self._get('BankTransactions', params)
        if result:
            return result.get('BankTransactions', [])
        return []

    def get_accounts(self) -> List[dict]:
        """Get chart of accounts"""
        result = self._get('Accounts')
        if result:
            return result.get('Accounts', [])
        return []

    def get_organisation(self) -> Optional[dict]:
        """Get organisation info"""
        result = self._get('Organisation')
        if result:
            orgs = result.get('Organisations', [])
            return orgs[0] if orgs else None
        return None

    def get_profit_loss(self, from_date: datetime, to_date: datetime) -> Optional[dict]:
        """Get profit and loss report"""
        params = {
            'fromDate': from_date.strftime('%Y-%m-%d'),
            'toDate': to_date.strftime('%Y-%m-%d')
        }
        return self._get('Reports/ProfitAndLoss', params)

    def get_balance_sheet(self) -> Optional[dict]:
        """Get balance sheet"""
        return self._get('Reports/BalanceSheet')

    # ===== Financial Summary Methods =====

    def get_weekly_summary(self) -> dict:
        """Get financial summary for the past week"""
        week_ago = datetime.now() - timedelta(days=7)

        # Get paid invoices this week
        paid = self.get_paid_invoices(since_date=week_ago)
        revenue = sum(float(inv.get('Total', 0)) for inv in paid)

        # Get unpaid invoices
        unpaid = self.get_unpaid_invoices()
        outstanding = sum(float(inv.get('AmountDue', 0)) for inv in unpaid)

        # Get bank transactions
        transactions = self.get_bank_transactions(since_date=week_ago)
        income = sum(float(t.get('Total', 0)) for t in transactions if t.get('Type') == 'RECEIVE')
        expenses = sum(float(t.get('Total', 0)) for t in transactions if t.get('Type') == 'SPEND')

        return {
            'period': f"{week_ago.strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}",
            'invoices_paid': len(paid),
            'revenue': revenue,
            'invoices_outstanding': len(unpaid),
            'outstanding_amount': outstanding,
            'income': income,
            'expenses': expenses,
            'net': income - expenses,
            'transactions': len(transactions)
        }

    def get_monthly_summary(self) -> dict:
        """Get financial summary for current month"""
        today = datetime.now()
        month_start = today.replace(day=1)

        paid = self.get_paid_invoices(since_date=month_start)
        revenue = sum(float(inv.get('Total', 0)) for inv in paid)

        unpaid = self.get_unpaid_invoices()
        outstanding = sum(float(inv.get('AmountDue', 0)) for inv in unpaid)

        return {
            'month': today.strftime('%B %Y'),
            'invoices_paid': len(paid),
            'revenue': revenue,
            'invoices_outstanding': len(unpaid),
            'outstanding_amount': outstanding
        }

    def format_for_briefing(self) -> str:
        """Format financial data for CEO briefing"""
        weekly = self.get_weekly_summary()
        monthly = self.get_monthly_summary()

        return f"""### Revenue (from Xero)

**This Week**:
- Invoices paid: {weekly['invoices_paid']}
- Revenue: ${weekly['revenue']:,.2f}
- Net (income - expenses): ${weekly['net']:,.2f}

**Month to Date** ({monthly['month']}):
- Invoices paid: {monthly['invoices_paid']}
- Revenue: ${monthly['revenue']:,.2f}

**Outstanding**:
- Unpaid invoices: {monthly['invoices_outstanding']}
- Amount due: ${monthly['outstanding_amount']:,.2f}

**Transactions this week**: {weekly['transactions']}
"""


def test_connection():
    """Test Xero connection"""
    client = XeroClient()

    if not client.access_token:
        print("❌ Not authenticated. Run: python auth/xero.py")
        return False

    org = client.get_organisation()
    if org:
        print(f"✅ Connected to: {org.get('Name')}")
        print(f"   Country: {org.get('CountryCode')}")
        print(f"   Currency: {org.get('BaseCurrency')}")

        # Get summary
        print("\n📊 Financial Summary:")
        print(client.format_for_briefing())
        return True
    else:
        print("❌ Could not fetch organisation info")
        return False


if __name__ == '__main__':
    test_connection()
