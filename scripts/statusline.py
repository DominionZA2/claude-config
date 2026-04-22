#!/usr/bin/env python3
"""Cross-platform Claude Code status line: [folder] branch · Xk/Ym (Z%)"""
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

ctx = data.get("context_window") or {}
used = ctx.get("total_input_tokens")
size = ctx.get("context_window_size")
pct = ctx.get("used_percentage")

parts = [f"[{folder}]"]
if branch:
    parts.append(branch)
if used is not None and size:
    parts.append(f"· {round(used/1000)}k/{round(size/1_000_000)}m ({round(pct or 0)}%)")

print(" ".join(parts))
