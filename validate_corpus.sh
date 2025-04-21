#!/bin/bash

# Script to validate the metropole_corpus.json file

# Set the script to exit on error
set -e

echo "=== Metropole Corpus Validation ==="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is required but not installed."
    exit 1
fi

# Check if the corpus file exists
if [ ! -f "data/processed/metropole_corpus.json" ]; then
    echo "Error: Corpus file not found at data/processed/metropole_corpus.json"
    echo "Make sure to run the add_metadata_and_tags.py script first."
    exit 1
fi

echo "Installing required dependencies..."
pip3 install -r requirements.txt

echo
echo "Running corpus validation tests..."
echo

# Run the test suite
python3 -m app.crawler.test_metropole_corpus

# Check the exit code
if [ $? -eq 0 ]; then
    echo
    echo "=== Validation Successful! ==="
    echo "The metropole_corpus.json file passed all validation tests."
else
    echo
    echo "=== Validation Failed! ==="
    echo "The metropole_corpus.json file failed some validation tests."
    exit 1
fi
