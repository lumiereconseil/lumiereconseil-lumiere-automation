import json
from datetime import datetime

def log_result(result: dict):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "result": result
    }

    with open("automation_log.json", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

