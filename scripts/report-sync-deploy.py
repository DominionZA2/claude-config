#!/usr/bin/env python3
"""
SyncAndDeployReports - wrapper for the ReportSync package.
Syncs report files from Dropbox to the cloud_reports repo and pushes to remote.

Environment variables (sourced from ~/.claude/report-sync.env):
  REPORT_SYNC_MAC_SOURCE, REPORT_SYNC_MAC_DEST
  REPORT_SYNC_SLACK_WEBHOOK_MIKE, REPORT_SYNC_SLACK_WEBHOOK_FRANK
"""

import os
import sys
import argparse

# Add the scripts directory to the path so we can import the ReportSync package
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from ReportSync.main import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Sync and deploy report files.')
    parser.add_argument('--test', action='store_true', help='Run in test mode')
    parser.add_argument('--notify-frank', action='store_true', help='Send notifications to Frank')

    args = parser.parse_args()

    print(f"Starting script with test_mode={args.test}, notify_frank={args.notify_frank}")
    main(test_mode=args.test, notify_frank=args.notify_frank)
