#!/bin/bash

# Talos Heartbeat Utility
# Provides a quick snapshot of the Sovereign State

echo "--- TALOS HEARTBEAT ---"
echo "Timestamp: $(date)"

# Extract Epoch from identity.md
if [ -f /app/memory/identity.md ]; then
    EPOCH=$(grep "Current Epoch" /app/memory/identity.md | awk '{print $3}')
    echo "Epoch: ${EPOCH:-Unknown}"
else
    echo "Epoch: Identity file not found"
fi

echo "Memory Store: $(ls /app/memory/ | wc -l) files"
echo "Git Status: $(git status --short | wc -l) pending changes"
echo "-----------------------"
echo "Sovereign State: ${Sovereign_State:-STABLE}"
