#!/usr/bin/env python3
"""Test approval workflow - runs one cycle of local orchestrator"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load env
load_dotenv()

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Import local orchestrator
from agents.local_orchestrator import LocalOrchestrator

def main():
    print("=" * 70)
    print("TESTING APPROVAL WORKFLOW")
    print("=" * 70)

    orchestrator = LocalOrchestrator()

    print("\n📋 Checking /Approved/ folder...")
    approved_dir = Path(os.getenv('VAULT_PATH', './vault')) / 'Approved'
    approved_files = list(approved_dir.glob('*.md'))

    print(f"Found {len(approved_files)} approved files:")
    for f in approved_files:
        print(f"  - {f.name}")

    if not approved_files:
        print("\n❌ No approved files found!")
        return 1

    print("\n🔄 Running one approval cycle...")
    print("-" * 70)

    # Run one cycle
    orchestrator.run_approval_cycle()

    print("-" * 70)
    print("\n✅ Cycle complete!")

    print("\n📁 Checking /Done/ folder...")
    done_dir = Path(os.getenv('VAULT_PATH', './vault')) / 'Done'
    done_files = list(done_dir.glob('*.md'))

    print(f"Files in /Done/: {len(done_files)}")
    for f in done_files:
        print(f"  - {f.name}")

    print("\n📊 Audit Log:")
    logs_dir = Path(os.getenv('VAULT_PATH', './vault')) / 'Logs'
    log_file = logs_dir / f"local_{Path.cwd().name}.jsonl"

    if log_file.exists():
        with open(log_file) as f:
            lines = f.readlines()
            for line in lines[-5:]:  # Last 5 lines
                print(f"  {line.rstrip()}")

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

    return 0

if __name__ == '__main__':
    sys.exit(main())
