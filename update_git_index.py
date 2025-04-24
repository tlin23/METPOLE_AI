#!/usr/bin/env python3
"""
Script to update .gitignore to only include the latest Chroma index directory.
This script identifies the most recently modified index directory and updates
the .gitignore file to exclude all other index directories.
"""

import re
from pathlib import Path

# Path to the index directory
INDEX_DIR = Path("./data/index")
# Path to the .gitignore file
GITIGNORE_PATH = Path("./.gitignore")


def get_latest_index_directory():
    """
    Identify the latest index directory based on modification time.

    Returns:
        Path: Path to the latest index directory, or None if no directories found.
    """
    if not INDEX_DIR.exists() or not INDEX_DIR.is_dir():
        print(
            f"Error: Index directory {INDEX_DIR} does not exist or is not a directory."
        )
        return None

    # Get all UUID directories in the index directory
    uuid_dirs = [
        d
        for d in INDEX_DIR.iterdir()
        if d.is_dir()
        and re.match(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", d.name
        )
    ]

    if not uuid_dirs:
        print("No index directories found.")
        return None

    # Find the most recently modified directory
    latest_dir = max(
        uuid_dirs,
        key=lambda d: max(
            (f.stat().st_mtime for f in d.glob("**/*") if f.is_file()),
            default=d.stat().st_mtime,
        ),
    )

    return latest_dir


def update_gitignore(latest_dir):
    """
    Update the .gitignore file to exclude all index directories except the latest one.

    Args:
        latest_dir (Path): Path to the latest index directory.
    """
    if not latest_dir:
        return

    # Read the current .gitignore file
    if GITIGNORE_PATH.exists():
        with open(GITIGNORE_PATH, "r") as f:
            gitignore_content = f.read()
    else:
        gitignore_content = ""

    # Define the markers for our managed section
    start_marker = "# BEGIN MANAGED CHROMA INDEX SECTION"
    end_marker = "# END MANAGED CHROMA INDEX SECTION"

    # Create the new section content
    latest_dir_relative = latest_dir.relative_to(Path("."))
    new_section = f"""
{start_marker}
# Only include the latest index directory
data/index/*
!data/index/chroma.sqlite3
!{latest_dir_relative}/
{end_marker}
"""

    # Ensure the content ends with a newline to satisfy end-of-file-fixer
    if not new_section.endswith("\n"):
        new_section += "\n"

    # Remove excessive blank lines at the end of the file
    gitignore_content = gitignore_content.rstrip("\n") + "\n\n"

    # Check if the managed section already exists
    start_pos = gitignore_content.find(start_marker)
    end_pos = gitignore_content.find(end_marker)

    if start_pos != -1 and end_pos != -1:
        # Replace the existing section
        gitignore_content = (
            gitignore_content[:start_pos].rstrip("\n")
            + "\n\n"
            + new_section
            + gitignore_content[end_pos + len(end_marker) :].lstrip("\n")
        )
    else:
        # Append the new section
        gitignore_content = gitignore_content.rstrip("\n") + "\n\n" + new_section

    # Ensure the entire gitignore content ends with a newline
    if not gitignore_content.endswith("\n"):
        gitignore_content += "\n"

    # Write the updated content back to the .gitignore file
    with open(GITIGNORE_PATH, "w") as f:
        f.write(gitignore_content)

    print(
        f"Updated .gitignore to only include the latest index directory: {latest_dir.name}"
    )


def main():
    """Main function to update the .gitignore file."""
    print(f"Identifying latest index directory in {INDEX_DIR}...")
    latest_dir = get_latest_index_directory()

    if latest_dir:
        print(f"Latest index directory: {latest_dir.name}")
        update_gitignore(latest_dir)
    else:
        print("No action taken.")


if __name__ == "__main__":
    main()
