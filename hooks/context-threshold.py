#!/usr/bin/env python3
"""Notify when a session's context usage crosses configured thresholds.

Wired (globally) to PostToolUse and Stop hooks. On each run it reads the
session transcript, computes how much of the context window is in use, and the
FIRST time usage crosses each threshold it (a) prints a systemMessage that the
Claude Code UI shows inline and (b) fires a native macOS notification banner.

Each threshold notifies once per session; state is kept in
~/.claude/hooks/state/ctx-<session_id>.json.
"""

import json
import os
import subprocess
import sys

# Percent-of-window thresholds to notify on, in ascending order. Each entry:
#   percent  - the % of the context window that triggers it
#   message  - the text shown (both in Claude and in the macOS notification)
#   style    - "banner": subtle macOS notification banner
#              "critical": red, centered macOS pop-up dialog you must dismiss
#   emoji    - prefix for the inline Claude message
THRESHOLDS = [
    {
        "percent": 50,
        "message": "Context usage is getting a bit high.",
        "style": "banner",
        "emoji": "⚠️",   # ⚠️
    },
    {
        "percent": 60,
        "message": ("Context is high — we're heading into the dumb zone. "
                    "Wrap up or /compact ASAP."),
        "style": "critical",
        "emoji": "\U0001f6d1",     # 🛑
    },
]

# Per-model context window (tokens). The transcript stores the bare model id
# (e.g. "claude-opus-4-8") without the [1m] beta marker, so we can't tell a
# 200k session from a 1M one by name alone. This user runs Opus 4.8 with the
# 1M-context beta, so default it to 1M; everything else to 200k. Edit freely.
MODEL_WINDOWS = {
    "claude-fable-5": 1_000_000,
    "claude-opus-4-8": 1_000_000,
}
DEFAULT_WINDOW = 200_000

STATE_DIR = os.path.expanduser("~/.claude/hooks/state")


def read_input():
    try:
        return json.loads(sys.stdin.read() or "{}")
    except Exception:
        return {}


def latest_usage_and_model(transcript_path):
    """Return (used_tokens, model) from the last assistant message with usage."""
    used, model = None, None
    try:
        with open(transcript_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or '"usage"' not in line:
                    continue
                try:
                    entry = json.loads(line)
                except Exception:
                    continue
                msg = entry.get("message") or {}
                if msg.get("role") != "assistant":
                    continue
                usage = msg.get("usage") or {}
                if not usage:
                    continue
                total = (
                    usage.get("input_tokens", 0)
                    + usage.get("cache_creation_input_tokens", 0)
                    + usage.get("cache_read_input_tokens", 0)
                )
                if total > 0:
                    used = total
                    model = msg.get("model") or model
    except Exception:
        return None, None
    return used, model


def window_for(model, used):
    window = MODEL_WINDOWS.get(model, DEFAULT_WINDOW)
    # Safety net: if we've already used more than the assumed window, the
    # session clearly has a larger one — bump to 1M so the percentage is sane.
    if used and used > window:
        window = 1_000_000
    return window


def load_fired(session_id):
    path = os.path.join(STATE_DIR, f"ctx-{session_id}.json")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return set(json.load(fh)), path
    except Exception:
        return set(), path


def save_fired(path, fired):
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(sorted(fired), fh)
    except Exception:
        pass


def notify_macos(style, title, message):
    """Fire a macOS notification. style="banner" is a subtle corner banner;
    style="critical" is a red, centered pop-up dialog (red stop icon)."""
    safe = message.replace('"', "'")
    safe_title = title.replace('"', "'")
    try:
        if style == "critical":
            # Centered modal dialog with the red stop icon. Launched detached
            # so the blocking dialog never holds up the hook; auto-dismisses
            # after 60s if the user ignores it.
            script = (f'display dialog "{safe}" with title "{safe_title}" '
                      f'with icon stop buttons {{"OK"}} default button "OK" '
                      f'giving up after 60')
            subprocess.Popen(
                ["osascript", "-e", script],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        else:
            subprocess.run(
                ["osascript", "-e",
                 f'display notification "{safe}" with title "{safe_title}"'],
                check=False, capture_output=True, timeout=5,
            )
    except Exception:
        pass


def main():
    data = read_input()
    transcript_path = data.get("transcript_path")
    session_id = data.get("session_id") or "unknown"
    if not transcript_path or not os.path.exists(transcript_path):
        return

    used, model = latest_usage_and_model(transcript_path)
    if not used:
        return

    window = window_for(model, used)
    pct = used / window * 100.0

    fired, state_path = load_fired(session_id)
    newly = [t for t in THRESHOLDS
             if pct >= t["percent"] and t["percent"] not in fired]
    if not newly:
        return

    fired.update(t["percent"] for t in newly)
    save_fired(state_path, fired)

    used_k = used / 1000.0
    win_k = window / 1000.0
    suffix = f" ({pct:.0f}% · {used_k:.0f}k/{win_k:.0f}k)"

    # Fire a macOS notification for each newly-crossed threshold.
    for t in newly:
        notify_macos(t["style"], f"Claude context — {t['percent']}%",
                     t["message"] + suffix)

    # Inline Claude message reflects the highest threshold just crossed.
    top = newly[-1]
    print(json.dumps(
        {"systemMessage": f"{top['emoji']}  {top['message']}{suffix}"}))


if __name__ == "__main__":
    main()
