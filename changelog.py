import json
from datetime import datetime

CHANGELOG_FILE = "changelog.jsonl"

def log_change(change_type: str, description: str, before_score: float, after_score: float, author: str = "jivitesh"):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "change_type": change_type,
        "description": description,
        "before_score": before_score,
        "after_score": after_score,
        "impact": round(after_score - before_score, 2),
        "author": author
    }
    with open(CHANGELOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"Logged: {change_type} | Impact: {entry['impact']:+.2f}")

if __name__ == "__main__":
    log_change(
        change_type="prompt_update",
        description="Added EMI suggestion to CANT_PAY prompt",
        before_score=7.0,
        after_score=8.5,
        author="jivitesh"
    )
