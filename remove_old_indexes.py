#!/usr/bin/env python3
"""
Script to remove old Chroma index directories from Git tracking.
This script identifies all index directories except the latest one
and removes them from Git tracking (but keeps them on the filesystem).
"""

import subprocess
import re
from pathlib import Path

# Path to the index directory
INDEX_DIR = Path("./data/index")
# Latest index directory (from our previous script)
LATEST_INDEX = "11f766eb-7fbb-4595-abfd-e13624aa4c44"


def get_tracked_index_directories():
    """
    Get all index directories currently tracked by Git.

    Returns:
        list: List of directory names (UUIDs) that are tracked by Git.
    """
    # Run git ls-files to get all tracked files in the data/index directory
    result = subprocess.run(
        ["git", "ls-files", "data/index/"], capture_output=True, text=True, check=True
    )

    # Extract directory names from the output
    tracked_files = result.stdout.strip().split("\n")

    # Extract unique directory names (UUIDs)
    uuid_pattern = (
        r"data/index/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/"
    )
    tracked_dirs = set()

    for file_path in tracked_files:
        match = re.match(uuid_pattern, file_path)
        if match:
            tracked_dirs.add(match.group(1))

    return tracked_dirs


def remove_from_git(directories):
    """
    Remove the specified directories from Git tracking.

    Args:
        directories (list): List of directory names (UUIDs) to remove.
    """
    for dir_name in directories:
        # Skip the latest index directory
        if dir_name == LATEST_INDEX:
            continue

        # Remove the directory from Git tracking
        dir_path = f"data/index/{dir_name}"
        print(f"Removing {dir_path} from Git tracking...")

        subprocess.run(["git", "rm", "--cached", "-r", dir_path], check=True)


def main():
    """Main function to remove old index directories from Git tracking."""
    print("Identifying tracked index directories...")
    tracked_dirs = get_tracked_index_directories()

    print(f"Found {len(tracked_dirs)} tracked index directories.")
    print(f"Latest index directory: {LATEST_INDEX}")

    # Filter out the latest directory
    dirs_to_remove = [d for d in tracked_dirs if d != LATEST_INDEX]

    if dirs_to_remove:
        print(
            f"Removing {len(dirs_to_remove)} old index directories from Git tracking:"
        )
        for dir_name in dirs_to_remove:
            print(f"  - {dir_name}")

        remove_from_git(dirs_to_remove)

        print("\nDone! The old index directories have been removed from Git tracking.")
        print(
            "They still exist on your filesystem, but won't be included in future commits."
        )
        print("To complete the process, commit these changes:")
        print('  git commit -m "Remove old index directories from Git tracking"')
    else:
        print("No old index directories to remove.")


if __name__ == "__main__":
    main()
