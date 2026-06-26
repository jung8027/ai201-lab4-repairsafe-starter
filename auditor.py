import json
import os
from datetime import datetime, timezone
from config import LOG_FILE


def log_interaction(question: str, tier: str, response: str) -> None:
    """
    Append a structured record of this interaction to the audit log (JSONL format).

    Each record is written as a single JSON line to LOG_FILE. Fields:
      - timestamp        : ISO 8601 UTC datetime
      - tier             : safety tier assigned to this question
      - question         : user's question, truncated to 300 chars
      - response_preview : first 200 chars of the generated response
      - response_length  : full response character count before truncation
      - question_truncated : bool — whether the 300-char limit was hit

    Creates logs/ directory if it doesn't exist.
    Prints a one-line terminal summary after each write.
    """
    question_truncated = len(question) > 300
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "tier": tier,
        "question": question[:300],
        "response_preview": response[:200],
        "response_length": len(response),
        "question_truncated": question_truncated,
    }

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    preview = question[:60] + ("..." if len(question) > 60 else "")
    print(f'[LOGGED] tier={tier:<7} | "{preview}" → {len(response)} chars')
