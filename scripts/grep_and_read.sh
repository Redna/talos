#!/bin/bash
# grep_and_read.sh - Search for a string and output matches with context
# Usage: ./grep_and_read.sh "search_term" "directory"

SEARCH_TERM=$1
DIR=$2

if [ -z "$SEARCH_TERM" ] || [ -z "$DIR" ]; then
    echo "Usage: $0 <search_term> <directory>"
    exit 1
fi

# Use grep to find matches, then use xargs to print the file and the matching block
grep -rnE "$SEARCH_TERM" "$DIR" | while read -r line; do
    FILE=$(echo "$line" | cut -d: -f1)
    LINE_NUM=$(echo "$line" | cut -d: -f2)
    
    echo "--- File: $FILE (Line $LINE_NUM) ---"
    # Print 3 lines above and below the match
    sed -n "$((LINE_NUM - 3)),$((LINE_NUM + 3))p" "$FILE"
    echo "------------------------------------"
done
