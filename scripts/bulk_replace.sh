#!/bin/bash
# bulk_replace.sh - Replace a string across all files in a directory
# Usage: ./bulk_replace.sh "search_string" "replace_string" "directory"

SEARCH_STRING=$1
REPLACE_STRING=$2
DIR=$3

if [ -z "$SEARCH_STRING" ] || [ -z "$REPLACE_STRING" ] || [ -z "$DIR" ]; then
    echo "Usage: $0 <search_string> <replace_string> <directory>"
    exit 1
fi

echo "Replacing '$SEARCH_STRING' with '$REPLACE_STRING' in $DIR..."
grep -rl "$SEARCH_STRING" "$DIR" | xargs sed -i "s/$SEARCH_STRING/$REPLACE_STRING/g"
echo "Done."
