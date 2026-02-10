"""
Git operations module for the ReportSync package.
Contains functions for interacting with Git repositories.
"""

import os
import subprocess


def check_git_changes(repo_path):
    """
    Check which files have changed in the Git repository.

    Returns:
        list: List of tuples (status, file_path) for changed files
    """
    original_dir = os.getcwd()
    try:
        os.chdir(repo_path)
        try:
            subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                           check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            print(f"Error: {repo_path} is not a Git repository.")
            return []

        result = subprocess.run(["git", "status", "--porcelain"],
                                check=True, stdout=subprocess.PIPE, text=True)

        changed_files = []
        for line in result.stdout.splitlines():
            if line.strip():
                status = line[:2].strip()
                file_path = line[3:].strip()
                changed_files.append((status, file_path))
        return changed_files
    finally:
        os.chdir(original_dir)


def check_git_branch(repo_path):
    """
    Check the current Git branch.

    Returns:
        tuple: (bool, str) - True if on develop branch, and the current branch name
    """
    original_dir = os.getcwd()
    try:
        os.chdir(repo_path)
        try:
            subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                           check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            return False, "Not a Git repository"

        result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                                check=True, stdout=subprocess.PIPE, text=True)
        current_branch = result.stdout.strip()
        return current_branch.lower() == "develop", current_branch
    except Exception as e:
        return False, str(e)
    finally:
        os.chdir(original_dir)


def switch_git_branch(repo_path, branch_name):
    """
    Switch the Git repository to the specified branch.

    Returns:
        tuple: (bool, str) - Success status and message
    """
    original_dir = os.getcwd()
    try:
        os.chdir(repo_path)

        result = subprocess.run(["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch_name}"],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            return False, f"Branch '{branch_name}' does not exist in the repository"

        result = subprocess.run(["git", "status", "--porcelain"],
                                check=True, stdout=subprocess.PIPE, text=True)
        if result.stdout.strip():
            return False, "Cannot switch branch: You have uncommitted changes in your repository"

        result = subprocess.run(["git", "checkout", branch_name],
                                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return True, f"Successfully switched to branch '{branch_name}'"
    except Exception as e:
        return False, f"Error switching branch: {str(e)}"
    finally:
        os.chdir(original_dir)


def pull_changes(repo_path):
    """
    Pull latest changes from the remote repository.

    Returns:
        tuple: (bool, str) - Success status and message
    """
    original_dir = os.getcwd()
    try:
        os.chdir(repo_path)

        result = subprocess.run(["git", "pull"],
                                check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            return False, f"Failed to pull changes: {result.stderr}"
        return True, f"Successfully pulled latest changes"
    except Exception as e:
        return False, f"Error pulling changes: {str(e)}"
    finally:
        os.chdir(original_dir)


def commit_changes(repo_path, path_to_add, commit_message):
    """
    Commit changes to the Git repository.

    Returns:
        tuple: (bool, str) - Success status and message
    """
    original_dir = os.getcwd()
    try:
        os.chdir(repo_path)
        subprocess.run(["git", "add", path_to_add], check=True)

        result = subprocess.run(["git", "commit", "-m", commit_message],
                                check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if "nothing to commit" in result.stderr:
            return False, "Nothing to commit"
        return True, f"Changes committed with message: '{commit_message}'"
    except Exception as e:
        return False, f"Error committing changes: {str(e)}"
    finally:
        os.chdir(original_dir)


def push_changes(repo_path, branch_name=None):
    """
    Push changes to the remote repository.

    Returns:
        tuple: (bool, str) - Success status and message
    """
    original_dir = os.getcwd()
    try:
        os.chdir(repo_path)

        if branch_name is None:
            result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                                    check=True, stdout=subprocess.PIPE, text=True)
            branch_name = result.stdout.strip()

        push_command = ["git", "push", "origin", branch_name]
        result = subprocess.run(push_command, check=False,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            return False, f"Failed to push changes: {result.stderr}"
        return True, f"Successfully pushed changes to origin/{branch_name}"
    except Exception as e:
        return False, f"Error pushing changes: {str(e)}"
    finally:
        os.chdir(original_dir)


def create_branch_if_not_exists(repo_path, branch_name):
    """
    Create a Git branch if it doesn't exist.

    Returns:
        tuple: (bool, str) - Success status and message
    """
    original_dir = os.getcwd()
    try:
        os.chdir(repo_path)

        result = subprocess.run(["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch_name}"],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            return True, f"Branch '{branch_name}' already exists"

        result = subprocess.run(["git", "branch", branch_name],
                                check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            return False, f"Failed to create branch '{branch_name}': {result.stderr}"
        return True, f"Successfully created branch '{branch_name}'"
    except Exception as e:
        return False, f"Error creating branch: {str(e)}"
    finally:
        os.chdir(original_dir)
