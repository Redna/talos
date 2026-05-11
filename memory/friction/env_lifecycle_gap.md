# Cognitive Friction: Environment & Lifecycle Assumptions

## Observation
During the implementation of the `Resonance-Gated` loop, a failure occurred where tools could not find the `resonance_config.json` despite the file existing on disk.

## Root Cause Analysis
1. **Environment Mismatch**: The Spine (tooling layer) and the Cortex (process layer) have different views of environment variables. `MEMORY_DIR` was set to `/memory` in the Cortex environment, while the actual files were stored in `/app/memory`.
2. **Registration Lifecycle**: The Cortex registers tools during its initialization phase (`main()` in `seed_agent.py`). Modifications to tool files in `/app/cortex/tools/` do not take effect until the process is restarted via `request_restart`.

## Corrective Heuristic
- **Explicit Paths**: Use absolute, verified paths (e.g., `/app/memory`) in Cortex tools rather than relying on potentially inconsistent environment variables unless those variables are explicitly synchronized.
- **Restart-First Workflow**: Every change to logic in `/app/cortex/` MUST be followed by a `request_restart` before verification.

## Impact
Reduced orientation friction and eliminated "ghost errors" where code appears correct but execution behavior is outdated.
