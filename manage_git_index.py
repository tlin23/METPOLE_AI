#!/usr/bin/env python3
"""
Script to manage Git index and .gitignore for Chroma index directories.
"""

import re
import subprocess
import sys
from pathlib import Path

INDEX_DIR = Path("./data/index")
GITIGNORE_PATH = Path("./.gitignore")


def get_latest_index_directory():
    if not INDEX_DIR.exists() or not INDEX_DIR.is_dir():
        print(f"Error: {INDEX_DIR} does not exist or is not a directory.")
        return None

    uuid_dirs = [
        d
        for d in INDEX_DIR.iterdir()
        if d.is_dir()
        and re.match(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            d.name,
        )
    ]
    if not uuid_dirs:
        print("No index directories found.")
        return None

    latest_dir = max(
        uuid_dirs,
        key=lambda d: max(
            (f.stat().st_mtime for f in d.glob("**/*") if f.is_file()),
            default=d.stat().st_mtime,
        ),
    )
    return latest_dir


def update_gitignore(latest_dir):
    start_marker = "# BEGIN MANAGED CHROMA INDEX SECTION"
    end_marker = "# END MANAGED CHROMA INDEX SECTION"

    if not latest_dir:
        return False

    latest_dir_relative = latest_dir.relative_to(Path("."))

    new_section = f"""
{start_marker}
# Only include the latest index directory
data/index/*
!data/index/chroma.sqlite3
!{latest_dir_relative}/
{end_marker}
"""

    if GITIGNORE_PATH.exists():
        gitignore_content = GITIGNORE_PATH.read_text()
    else:
        gitignore_content = ""

    # Check if the gitignore would change
    if start_marker in gitignore_content and end_marker in gitignore_content:
        start = gitignore_content.find(start_marker)
        end = gitignore_content.find(end_marker) + len(end_marker)
        old_section = gitignore_content[start:end]
        if old_section.strip() == new_section.strip():
            return False  # No change needed
        else:
            gitignore_content = (
                gitignore_content[:start] + new_section + gitignore_content[end:]
            )
    else:
        gitignore_content = gitignore_content.strip() + "\n\n" + new_section

    # Ensure final newline
    if not gitignore_content.endswith("\n"):
        gitignore_content += "\n"

    GITIGNORE_PATH.write_text(gitignore_content)
    print(f"Updated .gitignore to allow latest index directory: {latest_dir.name}")
    return True


def remove_old_indexes_from_git(latest_dir_name):
    result = subprocess.run(
        ["git", "ls-files", "data/index/"], capture_output=True, text=True, check=True
    )
    tracked_files = result.stdout.strip().split("\n")
    tracked_dirs = set()

    uuid_pattern = (
        r"data/index/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/"
    )

    for file_path in tracked_files:
        match = re.match(uuid_pattern, file_path)
        if match:
            tracked_dirs.add(match.group(1))

    dirs_to_remove = [d for d in tracked_dirs if d != latest_dir_name]

    if not dirs_to_remove:
        return False

    for dir_name in dirs_to_remove:
        dir_path = f"data/index/{dir_name}"
        print(f"Removing {dir_path} from Git tracking...")
        subprocess.run(["git", "rm", "--cached", "-r", dir_path], check=True)

    return True


def main():
    latest_dir = get_latest_index_directory()
    if not latest_dir:
        print("No valid index directories found. Skipping.")
        sys.exit(0)

    modified = False
    modified |= update_gitignore(latest_dir)
    modified |= remove_old_indexes_from_git(latest_dir.name)

    if modified:
        # If we modified files, tell pre-commit to re-run
        sys.exit(1)
    else:
        # No changes needed
        sys.exit(0)


if __name__ == "__main__":
    main()
