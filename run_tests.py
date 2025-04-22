#!/usr/bin/env python3
"""
Test runner script for Metropole AI test suite.
"""

import sys
import argparse
import subprocess


def run_tests(args):
    """Run the tests with the specified options."""
    # Base command
    cmd = ["pytest"]

    # Add verbosity
    if args.verbose:
        cmd.append("-v")

    # Add markers
    if args.marker:
        cmd.extend(["-m", args.marker])

    # Add coverage
    if args.coverage:
        cmd.extend(["--cov=app"])

        # Add coverage report format
        if args.html_report:
            cmd.extend(["--cov-report=html"])
        elif args.xml_report:
            cmd.extend(["--cov-report=xml"])
        else:
            cmd.extend(["--cov-report=term"])

    # Add specific test file or directory
    if args.test_path:
        cmd.append(args.test_path)
    else:
        cmd.append("tests/")

    # Print the command
    print(f"Running: {' '.join(cmd)}")

    # Run the command
    result = subprocess.run(cmd)
    return result.returncode


def main():
    """Parse arguments and run tests."""
    parser = argparse.ArgumentParser(description="Run Metropole AI tests")

    # Add arguments
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Increase verbosity"
    )
    parser.add_argument(
        "-m",
        "--marker",
        help="Run tests with specific marker (e.g., unit, integration, crawler)",
    )
    parser.add_argument(
        "-c", "--coverage", action="store_true", help="Run with coverage"
    )
    parser.add_argument(
        "--html-report", action="store_true", help="Generate HTML coverage report"
    )
    parser.add_argument(
        "--xml-report", action="store_true", help="Generate XML coverage report"
    )
    parser.add_argument(
        "test_path", nargs="?", help="Specific test file or directory to run"
    )

    # Parse arguments
    args = parser.parse_args()

    # Run tests
    return run_tests(args)


if __name__ == "__main__":
    sys.exit(main())
