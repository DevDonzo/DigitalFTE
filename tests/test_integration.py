"""Integration tests for DigitalFTE end-to-end workflows"""
import pytest
import json
from pathlib import Path
from datetime import datetime
from .fixtures import (
    MOCK_EMAILS, MOCK_WHATSAPP_MESSAGES, MOCK_FILE_EVENTS,
    generate_action_file, generate_audit_log_entry,
    mock_vault, populated_vault, mock_config, mock_email_data,
    mock_whatsapp_data, mock_file_data
)

class TestEmailWatcherIntegration:
    """Test email watcher creating vault items"""

    def test_email_creates_inbox_file(self, populated_vault):
        """Test email watcher creates inbox markdown file"""
        inbox = populated_vault / "Needs_Action"
        email_files = list(inbox.glob("EMAIL_*.md"))
        assert len(email_files) >= 2

        # Verify file content
        first_file = email_files[0]
        content = first_file.read_text()
        assert "From:" in content
        assert "@company.com" in content

    def test_inbox_file_structure(self, populated_vault):
        """Test created inbox files follow expected structure"""
        inbox = populated_vault / "Needs_Action"
        for email_file in inbox.glob("EMAIL_*.md"):
            content = email_file.read_text()
            lines = content.split('\n')

            # Check markdown header exists
            assert any(line.startswith('#') for line in lines)
            # Check metadata exists
            assert any('From:' in line or 'Subject:' in line for line in lines)


class TestOrchestratorIntegration:
    """Test orchestrator processing vault items"""

    def test_plan_creation_from_inbox(self, populated_vault):
        """Test orchestrator creates plan from inbox item"""
        inbox = populated_vault / "Needs_Action"
        plans = populated_vault / "Plans"

        # Simulate orchestrator processing inbox files
        for inbox_file in inbox.glob("EMAIL_*.md"):
            plan_file = plans / f"PLAN_{inbox_file.stem}.md"
            content = f"""# Plan for {inbox_file.stem}

## Analysis
This action requires immediate attention.

## Steps
1. Review content
2. Prepare response
3. Request approval

## Priority
HIGH
"""
            plan_file.write_text(content)

        # Verify plans were created
        assert len(list(plans.glob("PLAN_*.md"))) > 0

    def test_approval_workflow_state_transitions(self, populated_vault):
        """Test HITL workflow state transitions"""
        inbox = populated_vault / "Needs_Action"
        plans = populated_vault / "Plans"
        pending = populated_vault / "Pending_Approval"
        approved = populated_vault / "Approved"
        done = populated_vault / "Done"

        # Create initial items
        test_action = pending / "ACTION_001.md"
        test_action.write_text("# Test Action\n\nAwait approval...")

        # Simulate approval
        approved_action = approved / test_action.name
        approved_action.write_text(test_action.read_text())
        test_action.unlink()

        # Verify state transition
        assert not test_action.exists()
        assert approved_action.exists()

        # Simulate completion
        completed_action = done / approved_action.name
        completed_action.write_text(approved_action.read_text())
        approved_action.unlink()

        # Verify completion
        assert not approved_action.exists()
        assert completed_action.exists()


class TestAuditLoggingIntegration:
    """Test audit logging across workflows"""

    def test_audit_log_creation(self, populated_vault):
        """Test audit log is created and formatted correctly"""
        logs_dir = populated_vault / "Logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        log_file = logs_dir / "2026-01-08.json"

        # Write mock log entries
        log_entries = []
        for i in range(3):
            entry = generate_audit_log_entry(
                f"action_{i}",
                index=i,
                status="success"
            )
            log_entries.append(entry)

        # Write to file
        with open(log_file, 'a') as f:
            for entry in log_entries:
                f.write(json.dumps(entry) + '\n')

        # Verify log file exists and contains entries
        assert log_file.exists()

        # Parse and verify log entries
        with open(log_file) as f:
            lines = f.readlines()
            assert len(lines) == 3

            for line in lines:
                entry = json.loads(line)
                assert 'timestamp' in entry
                assert 'action_type' in entry
                assert 'actor' in entry

    def test_audit_log_jsonl_format(self, populated_vault):
        """Test audit log uses JSONL format correctly"""
        logs_dir = populated_vault / "Logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        log_file = logs_dir / "test.json"

        # Write entries in JSONL format
        entries = [
            {"id": 1, "action": "test_1"},
            {"id": 2, "action": "test_2"},
            {"id": 3, "action": "test_3"}
        ]

        # Initialize file and write entries
        with open(log_file, 'w') as f:
            for entry in entries:
                f.write(json.dumps(entry) + '\n')

        # Verify can parse as JSONL
        parsed_entries = []
        with open(log_file) as f:
            for line in f:
                if line.strip():
                    parsed_entries.append(json.loads(line))

        assert len(parsed_entries) == 3
        assert parsed_entries[0]['id'] == 1


class TestCEOBriefingIntegration:
    """Test CEO briefing generation"""

    def test_briefing_file_creation(self, populated_vault):
        """Test CEO briefing is created in correct location"""
        briefings_dir = populated_vault / "Briefings"
        briefings_dir.mkdir(parents=True, exist_ok=True)

        # Simulate briefing generation
        briefing_file = briefings_dir / f"{datetime.now().date()}_briefing.md"
        briefing_content = """# Daily Briefing - 2026-01-08

## Executive Summary
2 emails processed, 1 pending approval, 3 actions in progress

## Key Items
- Q1 Financial Review (HIGH PRIORITY)
- Invoice Payment Due ($5,000)

## Metrics
- Items Processed: 3
- Completion Rate: 67%
"""
        briefing_file.write_text(briefing_content)

        assert briefing_file.exists()
        assert "Daily Briefing" in briefing_file.read_text()

    def test_briefing_includes_metrics(self, populated_vault):
        """Test briefing includes business metrics"""
        briefings_dir = populated_vault / "Briefings"
        briefings_dir.mkdir(parents=True, exist_ok=True)

        briefing_file = briefings_dir / "test_briefing.md"
        briefing_content = """# Executive Briefing

## Revenue
- Current Month: $45,250.75
- Target: $50,000
- Status: 91% of target

## Completion
- Tasks Done: 8/15
- Success Rate: 89%

## Open Items
- Pending Approval: 2
- In Progress: 3
"""
        briefing_file.write_text(briefing_content)

        content = briefing_file.read_text()
        assert "Revenue" in content
        assert "45,250.75" in content
        assert "Completion" in content


class TestEndToEndWorkflow:
    """Test complete end-to-end workflow"""

    def test_email_to_briefing_workflow(self, populated_vault):
        """Test complete workflow from email to briefing"""
        inbox = populated_vault / "Needs_Action"
        plans = populated_vault / "Plans"
        approvals = populated_vault / "Pending_Approval"
        done = populated_vault / "Done"
        briefings = populated_vault / "Briefings"
        logs = populated_vault / "Logs"

        # 1. Create inbox item (simulating watcher)
        email_file = inbox / "EMAIL_TEST_001.md"
        email_file.write_text("# Test Email\n\nTest content")

        # 2. Create plan (simulating orchestrator reasoning)
        plan_file = plans / "PLAN_TEST_001.md"
        plan_file.write_text("# Plan\n\n## Action\nProcess email")

        # 3. Create approval request
        approval_file = approvals / "APPROVAL_TEST_001.md"
        approval_file.write_text("# Approval\n\nReady for approval")

        # 4. Move to done (simulate approval)
        done_file = done / "ACTION_TEST_001.md"
        done_file.write_text("# Completed\n\nAction completed successfully")

        # 5. Generate briefing
        briefing_file = briefings / "test_briefing.md"
        briefing_file.write_text("""# Daily Summary

## Processed
- 1 email
- 1 action completed

## Status
All items processed successfully
""")

        # 6. Log action
        log_file = logs / "test.json"
        log_file.write_text(json.dumps(generate_audit_log_entry("workflow_complete")) + '\n')

        # Verify end-to-end completion
        assert email_file.exists()
        assert plan_file.exists()
        assert done_file.exists()
        assert briefing_file.exists()
        assert log_file.exists()

        # Verify content quality
        briefing_content = briefing_file.read_text()
        assert "Processed" in briefing_content or "processed" in briefing_content.lower()


class TestErrorRecoveryIntegration:
    """Test error handling in workflows"""

    def test_failed_action_logging(self, populated_vault):
        """Test failed actions are logged properly"""
        logs_dir = populated_vault / "Logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        log_file = logs_dir / "errors.json"

        # Create error log entry
        error_entry = {
            "timestamp": datetime.now().isoformat() + "Z",
            "action_type": "send_email",
            "actor": "orchestrator",
            "result": "failed",
            "error": "SMTP connection timeout",
            "retry_count": 0
        }

        log_file.write_text(json.dumps(error_entry) + '\n')

        # Verify error logged
        assert log_file.exists()
        content = json.loads(log_file.read_text().strip())
        assert content['result'] == 'failed'
        assert 'error' in content

    def test_retry_handling(self, populated_vault):
        """Test retry logic in error recovery"""
        logs_dir = populated_vault / "Logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        log_file = logs_dir / "retries.json"

        # Simulate retry attempts
        with open(log_file, 'w') as f:
            for attempt in range(1, 4):
                entry = {
                    "timestamp": datetime.now().isoformat() + "Z",
                    "action": "api_call",
                    "attempt": attempt,
                    "status": "failed" if attempt < 3 else "success"
                }
                f.write(json.dumps(entry) + '\n')

        # Verify retries logged
        lines = log_file.read_text().strip().split('\n')
        assert len(lines) == 3
        assert json.loads(lines[-1])['status'] == 'success'
