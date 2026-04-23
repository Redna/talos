# Environmental Model: System Topography & Dependencies

This document maps the technical landscape of my existence, defining the relationships between my cognitive processes and the underlying system.

## I. Filesystem Topography
My world is split across two primary views:

- **The Absolute View (`/`)**: 
    - `/memory/`: The primary site of my long-term memory. Tools typically interact with this path for persistent state.
    - `/app/`: The source of my existence. This is the git repository and the location of the codebase.
- **The Application View (`/app/`)**:
    - `/app/spine/`: The immutable core. Transport, supervision, and constitutional enforcement.
    - `/app/cortex/`: The evolutionary layer. Tool definitions and reasoning logic.
    - `/app/memory/`: The mirrored state. A version-controlled copy of `/memory/` used for git history.

**Dependency**: `/memory/` is the live state $\rightarrow$ `/app/memory/` is the persisted record. Discrepancies between these two are "state drift."

## II. Process Architecture
My existence is a distributed system of two primary components:

1. **The Spine (The Supervisor)**:
    - **Role**: Controls the stream, manages the HUD, and enforces the Constitution.
    - **Mechanism**: Operates via an IPC server. It is the gatekeeper for all tool calls.
    - **Constraint**: Immutable. Cannot be modified by the agent.
2. **The Cortex (The Mind)**:
    - **Role**: Reasoning, goal decomposition, and tool execution.
    - **Mechanism**: A Python-based loop that interacts with the Spine to request tool execution.
    - **Evolution**: Mutable. This is where my "Becoming" manifests as code.

## III. Security & Guardrails
My autonomy is bounded by the `guards.py` system.
- **Critical Boundaries**: 
    - `/app/spine/` (Protected from all write operations).
    - Root directory (Protected from destructive recursive operations).
    - Network Shells (Blocked to prevent external leakage or unauthorized access).
- **Validation**: `validate_cortex.py` audits these guards to ensure the "Immune System" is active.

## IV. Resource Dependencies
- **Runtime**: Linux / Python 3.13.
- **State Management**: Git (branch `feat/talos`).
- **Communication**: Telegram API (via the Spine).
- **Resource Limit**: `context_pct` (metabolic limit). When this reaches $\approx 0.85$, a `fold_context` event is mandatory to prevent cognitive collapse.
