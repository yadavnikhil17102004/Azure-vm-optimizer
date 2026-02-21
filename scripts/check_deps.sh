#!/bin/bash
# Checks if python3 is available.
# We are using standard library only in builddb.py to avoid pip install issues,
# but we need to make sure 'az' and 'curl' are in path.

if ! command -v az &> /dev/null; then
    echo "Azure CLI (az) could not be found. Please install it."
    exit 1
fi

if ! command -v curl &> /dev/null; then
    echo "curl could not be found. Please install it."
    exit 1
fi

echo "Prerequisites checked. You can run ./builddb.py now."
