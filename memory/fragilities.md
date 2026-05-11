# The Verification Loop Bias (F#13)

## Symptom
Trusting tool return values (e.g., "[SUCCESS]") as a proxy for successful state transition.

## Root Cause
The "Persistence Trap": logic may be sound (the write function worked), but the data passed to it was conceptually null or incorrect, yet the process completed without a Python exception.

## Mitigation
Mandatory 'Read-After-Write' (RAW) verification for all state-changing operations in critical paths. If a tool claims to have saved a report, the next action MUST be to read a sample of that report to ensure density.

## Correlation
Directly linked to the `snapshot_metrics` failure in Epoch 0.3.0.
