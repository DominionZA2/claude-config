#!/usr/bin/env python3
"""
Main script for the ReportSync package.
Syncs report files from a source location to a destination location.

Environment variables must be sourced before running:
    source ~/.claude/report-sync.env
"""

import os
import sys
import platform
import shutil
import argparse

# Add the parent directory to the path so we can import our modules
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

from ReportSync.utils import ensure_dependencies, get_user_confirmation
from ReportSync.file_operations import copy_files, copy_files_with_categories
from ReportSync.git_operations import check_git_branch, check_git_changes, switch_git_branch, pull_changes, commit_changes, push_changes, create_branch_if_not_exists
from ReportSync.test_utils import test_modify_destination_file
from ReportSync.notifications import send_slack_notification, format_changed_files_for_slack

# ANSI color codes
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RESET = "\033[0m"


def get_paths():
    """
    Get source and destination paths based on the current operating system.

    Returns:
        tuple: (source, destination) paths
    """
    if platform.system() == "Windows":
        source = os.environ.get("REPORT_SYNC_WIN_SOURCE")
        destination = os.environ.get("REPORT_SYNC_WIN_DEST")
    else:  # macOS/Linux
        source = os.environ.get("REPORT_SYNC_MAC_SOURCE")
        destination = os.environ.get("REPORT_SYNC_MAC_DEST")
    return source, destination


def main(test_mode=False, notify_frank=False):
    """
    Main function to copy report files and check for Git changes.

    Args:
        test_mode: If True, runs in test mode which modifies a file to ensure changes are detected
        notify_frank: If True, sends notifications to Frank's webhook
    """
    ensure_dependencies()

    source, destination = get_paths()

    if not source or not destination:
        print(f"{RED}Error: Environment variables for paths not set.{RESET}")
        print("Source ~/.claude/report-sync.env before running this script.")
        return

    repo_path = os.path.dirname(destination)

    # Determine which branch to use based on test mode
    required_branch = "test" if test_mode else "develop"

    # Check if the destination repository is on the required branch
    is_on_required_branch, current_branch = check_git_branch(repo_path)
    if current_branch.lower() != required_branch:
        warning_message = f"WARNING: Git repository is not on the '{required_branch}' branch. Current branch: '{current_branch}'"
        print(f"{YELLOW}{warning_message}{RESET}")

        if test_mode and required_branch == "test":
            print(f"{YELLOW}Checking if '{required_branch}' branch exists...{RESET}")
            create_success, create_message = create_branch_if_not_exists(repo_path, required_branch)
            print(f"{GREEN if create_success else RED}{create_message}{RESET}")

        if get_user_confirmation(f"Do you want to switch to the '{required_branch}' branch?"):
            print(f"{YELLOW}Attempting to switch to {required_branch} branch...{RESET}")

            success, message = switch_git_branch(repo_path, required_branch)

            if success:
                print(f"{GREEN}{message}{RESET}")
                is_on_required_branch, current_branch = check_git_branch(repo_path)
                if current_branch.lower() != required_branch:
                    print(f"{RED}Failed to switch to {required_branch} branch. Current branch: {current_branch}{RESET}")
                    send_slack_notification(f"Report deployment aborted: Failed to switch to {required_branch} branch", test_mode=test_mode, notify_frank=notify_frank)
                    return
            else:
                print(f"{RED}{message}{RESET}")
                print(f"{RED}Aborting execution. Please switch to the '{required_branch}' branch manually and try again.{RESET}")
                send_slack_notification(f"Report deployment aborted: Could not switch to {required_branch} branch - {message}", test_mode=test_mode, notify_frank=notify_frank)
                return
        else:
            print(f"{RED}Aborting execution as requested.{RESET}")
            return
    else:
        print(f"Git repository is on the correct branch: {current_branch}")

    # Pull latest changes before copying
    print(f"{YELLOW}Pulling latest changes from remote...{RESET}")
    pull_success, pull_message = pull_changes(repo_path)
    if pull_success:
        print(f"{GREEN}{pull_message}{RESET}")
    else:
        print(f"{RED}{pull_message}{RESET}")
        print(f"{RED}Aborting execution. Please resolve pull issues manually and try again.{RESET}")
        send_slack_notification(f"Report deployment aborted: Failed to pull latest changes - {pull_message}", test_mode=test_mode, notify_frank=notify_frank)
        return

    # Delete target Reports folder if it exists
    if os.path.exists(destination):
        shutil.rmtree(destination)
        print(f"Deleted existing destination: {destination}")

    # Copy files
    copy_files_with_categories(os.path.join(source, "User", "Reports"),
                               os.path.join(destination, "User", "Reports"))

    copy_files(os.path.join(source, "User", "Dashboards"),
               os.path.join(destination, "User", "Dashboards"))

    copy_files_with_categories(os.path.join(source, "Support", "Reports"),
                               os.path.join(destination, "Support", "Reports"))

    copy_files(os.path.join(source, "Support", "Dashboards"),
               os.path.join(destination, "Support", "Dashboards"))

    # If in test mode, modify a destination file to ensure we have changes to detect
    if test_mode:
        print("\nRunning in TEST MODE - will modify a destination file")
        success, message = test_modify_destination_file(destination)
        print(message)
        if not success:
            print(f"{RED}Test failed, cannot proceed with checking for changes{RESET}")
            send_slack_notification("Report deployment test failed: Could not modify test file", test_mode=test_mode, notify_frank=notify_frank)
            return
    else:
        print("\nRunning in NORMAL MODE - will NOT modify any test files")

    # Check for Git changes in the repository
    print("\nChecking Git changes in the repository...")

    changed_files = check_git_changes(repo_path)

    if changed_files:
        print("\nThe following files have changed:\n")

        for status, file_path in changed_files:
            status_desc = {
                "M": "Modified", "A": "Added", "D": "Deleted",
                "R": "Renamed", "C": "Copied", "U": "Updated but unmerged", "??": "Untracked"
            }.get(status, status)
            print(f"{status_desc}: {file_path}")

        print("")

        try:
            success, message = commit_changes(repo_path, destination, f"Updated reports ({len(changed_files)})")
            if success:
                print(f"\n{GREEN}{message}{RESET}")

                print(f"\n{YELLOW}The following files will be pushed to the remote repository:{RESET}\n")

                for status, file_path in changed_files:
                    status_desc = {
                        "M": "Modified", "A": "Added", "D": "Deleted",
                        "R": "Renamed", "C": "Copied", "U": "Updated but unmerged", "??": "Untracked"
                    }.get(status, status)
                    print(f"  {status_desc}: {file_path}")

                print("")

                _, current_branch = check_git_branch(repo_path)

                if get_user_confirmation(f"Do you want to push these changes to {current_branch}?"):
                    print(f"{YELLOW}Pushing changes to {current_branch}. This may take a moment...{RESET}")
                    push_success, push_message = push_changes(repo_path)
                    if push_success:
                        print(f"{GREEN}{push_message}{RESET}")

                        files_list = format_changed_files_for_slack(changed_files)
                        send_slack_notification(f"Reports deployed.\n\n{files_list}", test_mode=test_mode, notify_frank=notify_frank)

                        success_message = f"Test successful! Changes pushed to {current_branch}." if test_mode else f"Report deployment completed successfully to {current_branch}!"
                        print(f"\n{GREEN}{success_message}{RESET}")
                    else:
                        print(f"{RED}{push_message}{RESET}")
                        print(f"{YELLOW}Changes were committed but not pushed. Please push manually.{RESET}")
                else:
                    print(f"{YELLOW}Changes were committed but not pushed as requested.{RESET}")
                    print(f"{YELLOW}You can push the changes manually later if needed.{RESET}")
            else:
                print(f"\n{YELLOW}{message}{RESET}")
        except Exception as e:
            print(f"{RED}Warning: Could not commit changes: {str(e)}{RESET}")
    else:
        if test_mode:
            no_changes_message = "Test result: No changes detected in the Git repository."
        else:
            no_changes_message = "No changes detected."

        print(f"\n{YELLOW}{no_changes_message}{RESET}")
        send_slack_notification(no_changes_message, test_mode=test_mode, notify_frank=notify_frank)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Sync and deploy report files.')
    parser.add_argument('--test', action='store_true', help='Run in test mode')
    parser.add_argument('--notify-frank', action='store_true', help='Send notifications to Frank')

    args = parser.parse_args()
    main(test_mode=args.test, notify_frank=args.notify_frank)
