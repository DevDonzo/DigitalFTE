#!/usr/bin/env python3
"""Run all tests and validations"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd, name):
    print(f"\n{'='*60}")
    print(f"Running: {name}")
    print('='*60)
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0

tests = [
    ("python3 Setup_Verify.py", "Setup Verification"),
    ("python3 -m pytest tests/ -v", "Unit Tests"),
    ("python3 scripts/weekly_audit.py", "CEO Briefing Generation"),
    ("python3 -m py_compile watchers/*.py", "Python Syntax Check"),
]

passed = 0
for cmd, name in tests:
    if run_command(cmd, name):
        passed += 1
        print(f"✅ {name} PASSED")
    else:
        print(f"❌ {name} FAILED")

print(f"\n{'='*60}")
print(f"Results: {passed}/{len(tests)} passed")
print('='*60)
sys.exit(0 if passed == len(tests) else 1)
