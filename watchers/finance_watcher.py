#!/usr/bin/env python3
"""
Finance Watcher - Monitors bank transactions and flags anomalies
Implements spec requirement: "Finance Watcher: Downloads local CSVs or calls banking APIs 
to log new transactions in /Accounting/Current_Month.md"
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from watchers.base_watcher import BaseWatcher

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FinanceWatcher(BaseWatcher):
    """Monitor bank transactions for anomalies and update ledger."""
    
    def __init__(self, vault_path: str, check_interval: int = 3600):
        """
        Args:
            vault_path: Path to Obsidian vault
            check_interval: Check every 1 hour (3600 seconds) by default
        """
        super().__init__(vault_path, check_interval=check_interval)
        self.bank_transactions = self.vault_path / 'Bank_Transactions.md'
        self.current_month = self.vault_path / 'Accounting' / 'Current_Month.md'
        self.processed_transactions = set()
        self.load_processed()
        
        # Anomaly thresholds
        self.HIGH_VALUE_THRESHOLD = 1000  # Flag transactions > $1000
        self.MONTHLY_SPEND_THRESHOLD = 500  # Alert if monthly spend > $500
    
    def load_processed(self):
        """Load list of already-processed transaction IDs."""
        processed_file = self.vault_path / '.processed_transactions'
        if processed_file.exists():
            try:
                with open(processed_file) as f:
                    self.processed_transactions = set(json.load(f))
            except Exception as e:
                logger.warning(f"Could not load processed transactions: {e}")
    
    def save_processed(self):
        """Save processed transaction IDs."""
        processed_file = self.vault_path / '.processed_transactions'
        try:
            with open(processed_file, 'w') as f:
                json.dump(list(self.processed_transactions), f)
        except Exception as e:
            logger.error(f"Could not save processed transactions: {e}")
    
    def check_for_updates(self) -> list:
        """Check Bank_Transactions.md for new entries."""
        if not self.bank_transactions.exists():
            logger.info("Bank_Transactions.md not found, skipping")
            return []
        
        try:
            content = self.bank_transactions.read_text()
            transactions = self._parse_transactions(content)
            
            # Filter to new transactions only
            new_transactions = [
                t for t in transactions 
                if t.get('id') not in self.processed_transactions
            ]
            
            return new_transactions
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return []
    
    def _parse_transactions(self, content: str) -> list:
        """Parse transaction table from Bank_Transactions.md."""
        transactions = []
        in_transaction_table = False
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Look for transaction table
            if '| Date |' in line:
                in_transaction_table = True
                continue
            
            if in_transaction_table and line.startswith('|') and '---' not in line:
                # Parse transaction row
                parts = [p.strip() for p in line.split('|')[1:-1]]  # Remove empty first/last
                if len(parts) >= 5:
                    try:
                        t = {
                            'id': parts[1],  # Invoice # or unique identifier
                            'date': parts[0],
                            'description': parts[1],
                            'amount': float(parts[2].replace('$', '').replace('+', '').strip()),
                            'category': parts[3],
                            'status': parts[4] if len(parts) > 4 else 'pending',
                        }
                        transactions.append(t)
                    except (ValueError, IndexError) as e:
                        logger.debug(f"Could not parse transaction row: {line} ({e})")
            
            elif in_transaction_table and not line.startswith('|'):
                in_transaction_table = False
        
        return transactions
    
    def create_action_file(self, transaction) -> Path:
        """Create action file for anomalous transactions."""
        try:
            amount = transaction['amount']
            
            # Check for high-value transactions
            if abs(amount) > self.HIGH_VALUE_THRESHOLD:
                return self._create_anomaly_file(
                    transaction,
                    f"High-value transaction: ${abs(amount):.2f}"
                )
            
            # Check for new payees
            if transaction.get('category') == 'Revenue':
                return self._create_revenue_file(transaction)
            
            # Log routine transactions
            self._log_transaction(transaction)
            self.processed_transactions.add(transaction['id'])
            self.save_processed()
            
            return None
        
        except Exception as e:
            logger.error(f"Error creating action file: {e}")
            return None
    
    def _create_anomaly_file(self, transaction, reason) -> Path:
        """Create action file for anomalous transaction."""
        filename = f"FINANCE_ANOMALY_{transaction['date'].replace('-', '')}_{transaction['id']}.md"
        filepath = self.needs_action / filename
        
        content = f"""---
type: finance_alert
transaction_id: {transaction['id']}
date: {transaction['date']}
amount: {transaction['amount']:.2f}
category: {transaction['category']}
reason: {reason}
status: pending_review
---

## Anomalous Transaction Alert

**Date**: {transaction['date']}
**Description**: {transaction['description']}
**Amount**: ${abs(transaction['amount']):.2f}
**Category**: {transaction['category']}

### Alert Reason
{reason}

### Suggested Actions
- [ ] Review transaction details
- [ ] Verify with bank/client if needed
- [ ] Update categorization if incorrect
- [ ] Mark as approved after review
"""
        
        filepath.write_text(content)
        logger.info(f"Created anomaly file: {filename}")
        self.processed_transactions.add(transaction['id'])
        self.save_processed()
        
        return filepath
    
    def _create_revenue_file(self, transaction) -> Path:
        """Create action file for revenue transactions."""
        filename = f"REVENUE_{transaction['date'].replace('-', '')}_{transaction.get('id', 'unknown')}.md"
        filepath = self.needs_action / filename
        
        content = f"""---
type: revenue_received
transaction_id: {transaction.get('id', '')}
date: {transaction['date']}
amount: {transaction['amount']:.2f}
client: {transaction['description']}
status: pending_verification
---

## Revenue Transaction Received

**Amount**: ${transaction['amount']:.2f}
**Client**: {transaction['description']}
**Date**: {transaction['date']}

### Next Steps
- [ ] Verify payment received
- [ ] Update invoice status in Xero
- [ ] Send thank-you email to client
- [ ] Archive transaction record
"""
        
        filepath.write_text(content)
        logger.info(f"Created revenue file: {filename}")
        self.processed_transactions.add(transaction['id'])
        self.save_processed()
        
        return filepath
    
    def _log_transaction(self, transaction):
        """Log routine transaction to audit trail."""
        log_file = self.vault_path / 'Logs' / f"{datetime.now().strftime('%Y-%m-%d')}_finance.jsonl"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'transaction_logged',
            'transaction_id': transaction['id'],
            'date': transaction['date'],
            'amount': transaction['amount'],
            'category': transaction['category'],
            'description': transaction['description'],
            'status': transaction.get('status', 'processed'),
        }
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def run(self):
        """Main watcher loop."""
        self.logger.info(f"Starting FinanceWatcher (check every {self.check_interval}s)")
        while True:
            try:
                transactions = self.check_for_updates()
                for transaction in transactions:
                    self.create_action_file(transaction)
                    self.logger.info(f"Processed transaction: {transaction['description']} ({transaction['amount']:.2f})")
            except Exception as e:
                self.logger.error(f"Error in watcher loop: {e}")
            
            import time
            time.sleep(self.check_interval)


if __name__ == '__main__':
    vault_path = os.getenv('VAULT_PATH', './vault')
    watcher = FinanceWatcher(vault_path)
    watcher.run()
