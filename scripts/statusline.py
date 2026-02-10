#!/usr/bin/env python3
"""Cross-platform Claude Code status line: [folder] branch"""
import json
import os
import subprocess
import sys

data = json.loads(sys.stdin.read())
folder = os.path.basename(data.get("workspace", {}).get("current_dir", ""))
try:
    branch = subprocess.check_output(
        ["git", "branch", "--show-current"],
        stderr=subprocess.DEVNULL, text=True
    ).strip()
except Exception:
    branch = ""

if branch:
    print(f"[{folder}] {branch}")
else:
    print(f"[{folder}]")
