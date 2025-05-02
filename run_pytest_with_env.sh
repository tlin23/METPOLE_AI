#!/bin/bash
export OPENAI_API_KEY=dummy-test-key
./venv/bin/python -m pytest tests/ --maxfail=1 --disable-warnings -q
