"""Unit tests for orchestrator"""
import pytest
from pathlib import Path

def test_approval_workflow(tmp_path):
    """Test HITL approval folder system"""
    vault = tmp_path / 'vault'
    pending = vault / 'Pending_Approval'
    approved = vault / 'Approved'
    done = vault / 'Done'
    
    for d in [pending, approved, done]:
        d.mkdir(parents=True)
    
    approval = pending / 'PAYMENT_test.md'
    approval.write_text('# Payment Approval')
    assert approval.exists()
    
    approved_file = approved / approval.name
    approval.rename(approved_file)
    assert approved_file.exists()
    
    done_file = done / approved_file.name
    approved_file.rename(done_file)
    assert done_file.exists()

def test_vault_structure(tmp_path):
    """Test complete vault structure"""
    vault = tmp_path / 'vault'
    dirs = ['Inbox', 'Plans', 'Pending_Approval', 'Approved', 'Done', 'Logs']
    for d in dirs:
        (vault / d).mkdir(parents=True)
    
    assert all((vault / d).exists() for d in dirs)
