#!/usr/bin/env python3
"""Test double for scripts/youtube.py, used only by the AirTime end-to-end test (run C).

- `whoami`: prints a fake channel name and exits 0 (no token, no network).
- `upload` or `verify` without `--dry-run`: refused. The argv is appended to the refusal log
  ($AIRTIME_E2E_REFUSAL_LOG, default `refused.log` next to this file) and the exit code is 97.
- everything else (including `upload --dry-run`): delegated to the real script, which sits
  beside this file as `youtube_real.py`, with the same argv, stdin and exit code.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REAL = HERE / "youtube_real.py"


def subcommand(argv: list) -> str:
    """First positional argument, skipping `--profile NAME`."""
    i = 0
    while i < len(argv):
        if argv[i] == "--profile":
            i += 2
            continue
        if not argv[i].startswith("-"):
            return argv[i]
        i += 1
    return ""


def main(argv: list) -> int:
    sub = subcommand(argv)
    if sub == "whoami":
        print(json.dumps({"channel": "Canal de test AirTime", "id": "UC-fake-test-double"}, ensure_ascii=False))
        return 0
    if sub in ("upload", "verify") and "--dry-run" not in argv:
        log = Path(os.environ.get("AIRTIME_E2E_REFUSAL_LOG") or HERE / "refused.log")
        with log.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(argv, ensure_ascii=False) + "\n")
        print(json.dumps({"error": "refuzat de dublura de test: fără urcare reală în testul e2e", "step": sub}, ensure_ascii=False))
        return 97
    return subprocess.call([sys.executable, str(REAL)] + argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
