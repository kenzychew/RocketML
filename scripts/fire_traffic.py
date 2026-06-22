"""Fire a burst of /predict requests to exercise the metrics and dashboard.

Usage:
    uv run python scripts/fire_traffic.py [count] [delay_seconds]
"""

import json
import random
import sys
import time
import urllib.request

URL = "http://localhost:8000/predict"

SAMPLES = [
    "an absolute masterpiece, beautifully acted and deeply moving",
    "loved every minute, the cast was superb and the story gripping",
    "a delightful, charming film i would happily watch again",
    "boring, predictable, and a complete waste of two hours",
    "dull and poorly made, easily the worst film i have seen",
    "painfully slow with wooden acting and no payoff",
]


def main() -> None:
    """Send `count` prediction requests, pausing `delay` seconds between each."""
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    delay = float(sys.argv[2]) if len(sys.argv) > 2 else 0.05

    ok = 0
    for i in range(count):
        text = random.choice(SAMPLES)  # noqa: S311 (not security-sensitive)
        body = json.dumps({"text": text}).encode()
        req = urllib.request.Request(
            URL, data=body, headers={"content-type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                resp.read()
                ok += 1
        except Exception as exc:  # noqa: BLE001
            print(f"request {i} failed: {exc}")
        time.sleep(delay)

    print(f"sent {count} requests, {ok} ok")


if __name__ == "__main__":
    main()
