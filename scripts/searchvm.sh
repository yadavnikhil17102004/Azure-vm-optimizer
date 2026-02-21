#!/bin/bash

DB_FILE="vms.json"

if [ ! -f "$DB_FILE" ]; then
    echo "Error: $DB_FILE not found. Run ./builddb.py first!"
    exit 1
fi

MAX_PRICE=$1

if [ -z "$MAX_PRICE" ]; then
    echo "Usage: ./searchvm.sh <max_hourly_price>"
    echo "Example: ./searchvm.sh 0.14"
    exit 1
fi

# Use jq to filter, sort, and format the output
jq -r --argjson budget "$MAX_PRICE" '
  map(select(.price <= $budget))
  | sort_by(.price)
  | .[]
  | "\(.region) | \(.sku) | \(.vcpu) vCPU | \(.ram) GB | $\(.price)/hr"
' "$DB_FILE" | column -t -s "|" | head -n 20

echo "..."
echo "Showing top 20 results (sorted by price cheapest first)."
