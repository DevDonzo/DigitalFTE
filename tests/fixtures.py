"""Test fixtures and mock data for integration testing"""
import json
from pathlib import Path
from datetime import datetime, timedelta

# Mock Gmail data
MOCK_EMAILS = [
    {
        "id": "EMAIL_001",
        "from": "boss@company.com",
        "to": "user@company.com",
        "subject": "Q1 Financial Review - ACTION NEEDED",
        "snippet": "Please review the attached financial statements for Q1...",
        "body": "Please review the attached Q1 financial statements and provide your analysis by end of week.",
        "timestamp": (datetime.now() - timedelta(hours=2)).isoformat() + "Z",
        "labels": ["INBOX", "IMPORTANT"],
        "is_unread": True
    },
    {
        "id": "EMAIL_002",
        "from": "finance@company.com",
        "to": "user@company.com",
        "subject": "Invoice #12345 Due - Payment Required",
        "snippet": "Invoice payment due by end of month...",
        "body": "Invoice #12345 from Acme Corp is due by Jan 31. Amount: $5,000.",
        "timestamp": (datetime.now() - timedelta(hours=4)).isoformat() + "Z",
        "labels": ["INBOX"],
        "is_unread": True
    },
    {
        "id": "EMAIL_003",
        "from": "hr@company.com",
        "to": "user@company.com",
        "subject": "Team Meeting - This Friday",
        "snippet": "Team sync meeting this Friday at 2pm...",
        "body": "Team sync meeting scheduled for Friday, Jan 10 at 2pm. Please confirm attendance.",
        "timestamp": (datetime.now() - timedelta(hours=24)).isoformat() + "Z",
        "labels": ["INBOX"],
        "is_unread": False
    }
]

# Mock WhatsApp messages
MOCK_WHATSAPP_MESSAGES = [
    {
        "id": "WHATSAPP_001",
        "from": "John (Boss)",
        "message": "URGENT: Need Q1 report asap",
        "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat() + "Z",
        "has_media": False,
        "keywords": ["URGENT", "asap"]
    },
    {
        "id": "WHATSAPP_002",
        "from": "Sarah (Finance)",
        "message": "Invoice INV-12345 payment status?",
        "timestamp": (datetime.now() - timedelta(minutes=45)).isoformat() + "Z",
        "has_media": False,
        "keywords": ["invoice", "payment"]
    },
    {
        "id": "WHATSAPP_003",
        "from": "Client Account",
        "message": "Help! Can't access dashboard",
        "timestamp": (datetime.now() - timedelta(minutes=60)).isoformat() + "Z",
        "has_media": False,
        "keywords": ["help"]
    }
]

# Mock file system events
MOCK_FILE_EVENTS = [
    {
        "id": "FILE_001",
        "filename": "Q1_Financial_Report.xlsx",
        "path": "/Users/user/Downloads/Q1_Financial_Report.xlsx",
        "size": 2457600,
        "type": "spreadsheet",
        "timestamp": (datetime.now() - timedelta(hours=1)).isoformat() + "Z",
        "action": "created"
    },
    {
        "id": "FILE_002",
        "filename": "Invoice_Summary_Jan.pdf",
        "path": "/Users/user/Downloads/Invoice_Summary_Jan.pdf",
        "size": 512000,
        "type": "document",
        "timestamp": (datetime.now() - timedelta(hours=2)).isoformat() + "Z",
        "action": "created"
    }
]

# Mock vault directory structure
MOCK_VAULT_STRUCTURE = {
    "Inbox": ["EMAIL_001.md", "EMAIL_002.md", "WHATSAPP_001.md", "FILE_001.md"],
    "Plans": ["PLAN_EMAIL_001.md", "PLAN_WHATSAPP_001.md"],
    "Needs_Action": ["ACTION_001.md"],
    "Pending_Approval": ["APPROVAL_001.md"],
    "Approved": [],
    "Rejected": [],
    "Done": ["ACTION_COMPLETED_001.md"],
    "Accounting": ["xero_config.md", "Current_Month.md"],
    "Briefings": ["2026-01-08_briefing.md"],
    "Social_Media": ["posting_schedule.md"],
    "Logs": ["2026-01-08.json"]
}

# Mock orchestrator plans
MOCK_PLANS = {
    "PLAN_EMAIL_001": {
        "title": "Process Q1 Financial Review",
        "source": "EMAIL_001",
        "reasoning": "Boss requires Q1 financial analysis. This is marked IMPORTANT and needs immediate attention.",
        "actions": [
            "Review attached financial statements",
            "Prepare analysis summary",
            "Request approvals if needed"
        ],
        "priority": "HIGH",
        "estimated_duration": "2 hours",
        "next_step": "Create response email with analysis"
    },
    "PLAN_WHATSAPP_001": {
        "title": "Urgent Report Request",
        "source": "WHATSAPP_001",
        "reasoning": "Urgent message from boss requesting Q1 report. Contains urgency markers.",
        "actions": [
            "Compile Q1 report",
            "Send via email/WhatsApp",
            "Confirm receipt"
        ],
        "priority": "CRITICAL",
        "estimated_duration": "1 hour",
        "next_step": "Gather report components and prepare delivery"
    }
}

# Mock approval workflow entries
MOCK_APPROVALS = {
    "APPROVAL_001": {
        "type": "email_response",
        "source_action": "PLAN_EMAIL_001",
        "recipient": "boss@company.com",
        "subject": "Re: Q1 Financial Review",
        "body": "Dear Boss,\n\nPlease find the Q1 financial analysis below:\n\nRevenue: $125,000\nExpenses: $45,000\nNet Profit: $80,000\n\nBest regards",
        "requires_approval": True,
        "created_at": (datetime.now() - timedelta(minutes=30)).isoformat() + "Z"
    }
}

# Mock briefing data
MOCK_BRIEFING = {
    "date": datetime.now().isoformat().split('T')[0],
    "executive_summary": "Active week with 3 urgent items requiring attention",
    "metrics": {
        "total_items_processed": 15,
        "items_pending_approval": 2,
        "items_completed": 8,
        "items_failed": 1,
        "completion_rate": 0.85
    },
    "key_actions": [
        "Q1 financial review from boss (HIGH PRIORITY)",
        "Invoice payment verification ($5,000 due)",
        "Customer support escalation - dashboard access issue"
    ],
    "revenue_summary": {
        "current_month": 45250.75,
        "target": 50000.00,
        "status": "On track"
    },
    "recommendations": [
        "Process Q1 review immediately",
        "Follow up on invoice payment",
        "Contact customer support for dashboard issue"
    ]
}

# Mock audit log entries
MOCK_AUDIT_LOGS = [
    {
        "timestamp": (datetime.now() - timedelta(hours=2)).isoformat() + "Z",
        "action_type": "email_received",
        "actor": "gmail_watcher",
        "result": "success",
        "details": {"email_id": "EMAIL_001", "from": "boss@company.com"}
    },
    {
        "timestamp": (datetime.now() - timedelta(hours=2, minutes=5)).isoformat() + "Z",
        "action_type": "plan_created",
        "actor": "orchestrator",
        "result": "success",
        "details": {"plan_id": "PLAN_EMAIL_001", "source": "EMAIL_001"}
    },
    {
        "timestamp": (datetime.now() - timedelta(hours=1, minutes=30)).isoformat() + "Z",
        "action_type": "approval_requested",
        "actor": "orchestrator",
        "result": "success",
        "details": {"approval_id": "APPROVAL_001", "action": "email_response"}
    }
]

# Test data generators
def generate_email(index: int = 1, **overrides) -> dict:
    """Generate mock email data"""
    base = {
        "id": f"EMAIL_{index:03d}",
        "from": f"sender{index}@company.com",
        "subject": f"Test Email {index}",
        "body": f"This is test email number {index}",
        "timestamp": datetime.now().isoformat() + "Z",
        "is_unread": True
    }
    base.update(overrides)
    return base

def generate_action_file(vault_path: Path, action_type: str = "inbox", **data):
    """Generate mock action file in vault"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = action_type.upper()

    filename = f"{prefix}_{timestamp}.md"
    if action_type == "inbox":
        directory = vault_path / "Inbox"
    elif action_type == "plan":
        directory = vault_path / "Plans"
    elif action_type == "approval":
        directory = vault_path / "Pending_Approval"
    else:
        directory = vault_path / action_type

    directory.mkdir(parents=True, exist_ok=True)
    filepath = directory / filename

    # Generate markdown content
    content = f"# {action_type.title()}\n\n"
    for key, value in data.items():
        if isinstance(value, dict):
            content += f"## {key.replace('_', ' ').title()}\n\n"
            for k, v in value.items():
                content += f"- **{k}**: {v}\n"
        else:
            content += f"- **{key.replace('_', ' ').title()}**: {value}\n"

    filepath.write_text(content)
    return filepath

def generate_audit_log_entry(action_type: str, **details) -> dict:
    """Generate audit log entry"""
    return {
        "timestamp": datetime.now().isoformat() + "Z",
        "action_type": action_type,
        "actor": "test_runner",
        "result": "success",
        "details": details
    }

# Fixture decorators for pytest
import pytest

@pytest.fixture
def mock_email_data():
    """Provide mock email data"""
    return MOCK_EMAILS

@pytest.fixture
def mock_whatsapp_data():
    """Provide mock WhatsApp data"""
    return MOCK_WHATSAPP_MESSAGES

@pytest.fixture
def mock_file_data():
    """Provide mock file event data"""
    return MOCK_FILE_EVENTS

@pytest.fixture
def mock_vault(tmp_path):
    """Create mock vault directory structure"""
    vault = tmp_path / "vault"
    for directory in MOCK_VAULT_STRUCTURE.keys():
        (vault / directory).mkdir(parents=True, exist_ok=True)
    return vault

@pytest.fixture
def populated_vault(mock_vault):
    """Create vault with sample files"""
    # Add inbox items
    inbox = mock_vault / "Inbox"
    for email in MOCK_EMAILS[:2]:
        filename = f"{email['id']}.md"
        content = f"# {email['subject']}\n\nFrom: {email['from']}\n\n{email['body']}"
        (inbox / filename).write_text(content)
    return mock_vault

@pytest.fixture
def mock_config(tmp_path):
    """Create mock configuration"""
    config = {
        "vault_path": str(tmp_path / "vault"),
        "gmail_enabled": True,
        "whatsapp_enabled": True,
        "filesystem_enabled": True,
        "orchestrator_enabled": True,
        "check_interval": 60
    }
    config_file = tmp_path / ".env"
    config_file.write_text("\n".join([f"{k.upper()}={v}" for k, v in config.items()]))
    return config
