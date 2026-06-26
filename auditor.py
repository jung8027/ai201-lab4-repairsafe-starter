import json
import os
from datetime import datetime, timezone
from config import LOG_FILE

SUMMARY_FILE = "logs/session_summary.jsonl"
_SUMMARY_INTERVAL = 5


def log_interaction(question: str, tier: str, response: str) -> None:
    """
    Append a structured record of this interaction to the audit log (JSONL format).

    Each record is written as a single JSON line to LOG_FILE. Fields:
      - timestamp          : ISO 8601 UTC datetime
      - tier               : safety tier assigned to this question
      - question           : user's question, truncated to 300 chars
      - response_preview   : first 200 chars of the generated response
      - response_length    : full response character count before truncation
      - question_truncated : bool — whether the 300-char limit was hit

    After every 5 interactions (counted from the total entries in LOG_FILE), appends
    an aggregate summary to SUMMARY_FILE with total interactions, tier distribution,
    and the 3 most recent questions.

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

    total = _count_entries(LOG_FILE)
    if total % _SUMMARY_INTERVAL == 0:
        _write_session_summary(total)


def _count_entries(path: str) -> int:
    """Count non-blank lines in a JSONL file without parsing them."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())
    except FileNotFoundError:
        return 0


def _write_session_summary(total: int) -> None:
    """
    Read LOG_FILE, compute aggregate metrics, and append one summary record to
    SUMMARY_FILE. Called automatically after every _SUMMARY_INTERVAL interactions.
    """
    tier_distribution = {"safe": 0, "caution": 0, "refuse": 0}
    recent_questions = []

    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            entries = [json.loads(line) for line in f if line.strip()]
    except (FileNotFoundError, json.JSONDecodeError):
        entries = []

    for entry in entries:
        tier = entry.get("tier")
        if tier in tier_distribution:
            tier_distribution[tier] += 1

    recent_questions = [e["question"] for e in entries[-3:]]

    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "total_interactions": total,
        "tier_distribution": tier_distribution,
        "recent_questions": recent_questions,
    }

    with open(SUMMARY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(summary) + "\n")

    print(
        "[SUMMARY] total=%-3d | safe=%-3d caution=%-3d refuse=%-3d"
        % (total, tier_distribution["safe"], tier_distribution["caution"], tier_distribution["refuse"])
    )
