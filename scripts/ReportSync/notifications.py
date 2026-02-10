"""
Notifications module for the ReportSync package.
Contains functions for sending notifications.
"""

import os
import json
import urllib.request


def send_slack_notification(message, test_mode=False, notify_frank=False):
    """
    Send a simple notification to Slack.

    Args:
        message: The message to send
        test_mode: If True, only sends to Mike's webhook
        notify_frank: If True, sends to Frank's webhook (when not in test mode)

    Returns:
        bool: True if the message was sent successfully, False otherwise
    """
    mike_webhook_url = os.environ.get("REPORT_SYNC_SLACK_WEBHOOK_MIKE", "")
    frank_webhook_url = os.environ.get("REPORT_SYNC_SLACK_WEBHOOK_FRANK", "")

    success = True

    # Send to Mike's webhook
    try:
        payload = json.dumps({"text": message}).encode("utf-8")
        req = urllib.request.Request(
            mike_webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req) as resp:
            if resp.status == 200:
                print("Slack notification sent to Mike's webhook")
            else:
                print(f"Failed to send Slack notification to Mike's webhook. Status code: {resp.status}")
                success = False
    except Exception as e:
        print(f"Error sending Slack notification to Mike's webhook: {str(e)}")
        success = False

    # Send to Frank's webhook if not in test mode AND notify_frank is True
    if not test_mode and notify_frank:
        try:
            payload = json.dumps({"text": message}).encode("utf-8")
            req = urllib.request.Request(
                frank_webhook_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req) as resp:
                if resp.status == 200:
                    print("Slack notification sent to Frank's webhook")
                else:
                    print(f"Failed to send Slack notification to Frank's webhook. Status code: {resp.status}")
                    success = False
        except Exception as e:
            print(f"Error sending Slack notification to Frank's webhook: {str(e)}")
            success = False

    return success


def format_changed_files_for_slack(changed_files):
    """
    Format the list of changed files for Slack notification.

    Returns:
        str: Formatted message with file names and their status
    """
    if not changed_files:
        return "No files changed"

    formatted_files = []
    for status, file_path in changed_files:
        filename = os.path.basename(file_path)
        if not filename:
            continue

        status_map = {"M": "(M)", "A": "(A)", "D": "(D)", "R": "(R)", "C": "(C)", "??": "(U)"}
        status_indicator = status_map.get(status, f"({status})")
        formatted_files.append(f"\u2022 {filename} {status_indicator}")

    return "\n".join(formatted_files)
