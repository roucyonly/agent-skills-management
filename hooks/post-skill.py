#!/usr/bin/env python3
"""PostToolUse hook for Skill tool. Records skill invocation end to usage.jsonl."""

import sys
import json
import os
from datetime import datetime

USAGE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "usage.jsonl"
)

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    skill_name = tool_input.get("skill", "unknown")
    session_id = data.get("session_id", "unknown")
    success = data.get("success", True)

    event = {
        "event": "skill_end",
        "ts": datetime.now().isoformat(),
        "session_id": session_id,
        "skill": skill_name,
        "success": bool(success)
    }

    try:
        with open(USAGE_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        pass

    sys.exit(0)

if __name__ == "__main__":
    main()
