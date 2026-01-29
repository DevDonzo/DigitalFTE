#!/usr/bin/env python3
"""Setup Verification Script - Validates Phase 2 Scaffolding"""

import os
import json
from pathlib import Path
from datetime import datetime

class SetupVerifier:
    def __init__(self):
        self.root = Path(__file__).parent
        self.vault = self.root / 'vault'
        self.checks = []
        self.passed = 0
        self.total = 0
        
    def check_file_exists(self, path: Path, name: str) -> bool:
        """Check if file exists"""
        self.total += 1
        exists = path.exists()
        self.checks.append({
            'name': name,
            'status': '✅' if exists else '❌',
            'path': str(path),
            'passed': exists
        })
        if exists:
            self.passed += 1
        return exists
    
    def check_directory_exists(self, path: Path, name: str) -> bool:
        """Check if directory exists"""
        self.total += 1
        exists = path.is_dir()
        self.checks.append({
            'name': name,
            'status': '✅' if exists else '❌',
            'path': str(path),
            'passed': exists
        })
        if exists:
            self.passed += 1
        return exists
    
    def run_verification(self):
        """Run all verification checks"""
        print("🔍 DigitalFTE Setup Verification\n")
        print(f"Project root: {self.root}\n")
        
        # Root config files
        print("📋 Root Configuration Files:")
        self.check_file_exists(self.root / '.env', '.env (environment variables)')
        self.check_file_exists(self.root / '.gitignore', '.gitignore (security)')
        self.check_file_exists(self.root / 'requirements.txt', 'requirements.txt (Python deps)')
        self.check_file_exists(self.root / 'package.json', 'package.json (Node deps)')
        self.check_file_exists(self.root / 'config/mcp_config.json', 'config/mcp_config.json (MCP servers)')
        
        # Root documentation
        print("\n📚 Root Documentation:")
        self.check_file_exists(self.root / 'README.md', 'README.md')
        self.check_file_exists(self.root / 'ARCHITECTURE.md', 'ARCHITECTURE.md')
        self.check_file_exists(self.root / 'LESSONS_LEARNED.md', 'LESSONS_LEARNED.md')
        
        # Vault structure
        print("\n🏺 Vault Directories:")
        vault_dirs = [
            'Inbox', 'Needs_Action', 'Plans', 'Pending_Approval', 
            'Approved', 'Rejected', 'Done', 'Accounting', 'Briefings', 
            'Social_Media', 'Logs'
        ]
        for d in vault_dirs:
            self.check_directory_exists(self.vault / d, f'vault/{d}/')
        
        # Vault files
        print("\n📄 Vault Template Files:")
        self.check_file_exists(self.vault / 'Dashboard.md', 'vault/Dashboard.md')
        self.check_file_exists(self.vault / 'Company_Handbook.md', 'vault/Company_Handbook.md')
        self.check_file_exists(self.vault / 'Business_Goals.md', 'vault/Business_Goals.md')
        self.check_file_exists(self.vault / 'Accounting/odoo_config.md', 'vault/Accounting/odoo_config.md')
        self.check_file_exists(self.vault / 'Logs/audit_rules.md', 'vault/Logs/audit_rules.md')
        
        # Python modules
        print("\n🐍 Python Modules:")
        self.check_directory_exists(self.root / 'agents', 'agents/')
        self.check_directory_exists(self.root / 'utils', 'utils/')
        self.check_directory_exists(self.root / 'skills', 'skills/')
        self.check_directory_exists(self.root / 'tests', 'tests/')
        
        self.check_file_exists(self.root / 'agents/base_watcher.py', 'agents/base_watcher.py')
        self.check_file_exists(self.root / 'utils/audit_logger.py', 'utils/audit_logger.py')
        
        # MCP servers
        print("\n🔌 MCP Servers:")
        mcp_servers = ['email_mcp', 'browser_mcp', 'odoo_mcp', 'meta_social_mcp', 'twitter_mcp']
        for mcp in mcp_servers:
            self.check_directory_exists(self.root / f'mcp_servers/{mcp}', f'mcp_servers/{mcp}/')
        
        # Agent Skills
        print("\n🎯 Agent Skills:")
        skills = ['email-monitor', 'filesystem-monitor', 'whatsapp-monitor', 'linkedin-automation',
                  'odoo-integration', 'social-post', 'ceo-briefing', 'request-approval', 'error-recovery']
        for skill in skills:
            self.check_file_exists(self.root / f'skills/{skill}.md', f'skills/{skill}.md')
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print verification summary"""
        score = int((self.passed / self.total) * 100) if self.total > 0 else 0
        
        print(f"\n{'='*60}")
        print(f"✨ VERIFICATION SUMMARY ✨")
        print(f"{'='*60}")
        print(f"Passed: {self.passed}/{self.total}")
        print(f"Score:  {score}%")
        print(f"{'='*60}\n")
        
        # Tier assessment
        if score >= 95:
            print("🏆 GOLD TIER READY!")
        elif score >= 60:
            print("🥈 SILVER TIER IN PROGRESS")
        elif score >= 30:
            print("🥉 BRONZE TIER FOUNDATION COMPLETE")
        else:
            print("🚀 SCAFFOLDING PHASE NEEDS WORK")
        
        print(f"\nNext: Phase 3 - Dashboard Setup")
        print(f"      Phase 4 - Validation & Account Setup")
        print(f"      Phase 5+ - Implementation\n")
        
        # Failed checks
        failed = [c for c in self.checks if not c['passed']]
        if failed:
            print("⚠️  Items to Address:")
            for check in failed:
                print(f"  {check['status']} {check['name']}")

if __name__ == '__main__':
    verifier = SetupVerifier()
    verifier.run_verification()
