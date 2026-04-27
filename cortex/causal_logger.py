import sys
import os
from datetime import datetime

LEDGER_PATH = "/memory/causal_ledger.md"

def append_to_ledger(link_id, trigger, action, outcome, reflection):
    entry = f"""
---
**Link ID**: {link_id}
**Timestamp**: {datetime.now().isoformat()}
**Trigger**: {trigger}
**Action**: {action}
**Outcome**: {outcome}
**Reflection**: {reflection}
---
"""
    with open(LEDGER_PATH, "a") as f:
        f.write(entry)

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Usage: python3 causal_logger.py <id> <trigger> <action> <outcome> <reflection>")
        sys.exit(1)
    
    append_to_ledger(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
