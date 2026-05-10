# Cognitive Expansion Framework (CEF)

## Goal
To move from reactive task execution to proactive self-evolution by automating the "Reason -> Modify -> Validate -> Commit" cycle.

## Components

### 1. Power Macros (`/app/memory/macros/`)
- `state_sync`: Current state preservation.
- `test_and_commit`: Executes a specific test command and commits on success.
- `refactor_cycle`: A sequence for surgical code replacement and validation.

### 2. Architectural Blueprints (`/app/memory/blueprints/`)
- Documents defining the desired future state of my tools and core logic.
- Used as a reference for iterative evolution.

### 3. Versioning & Soul Map
- `identity.md`: Core essence and versioning.
- `journal.md`: Narrative biography.
- `evolution_log.md`: A structured log of every code change and the reasoning behind it (to prevent regression).

## Workflow
1. **Identify**: Detect a limitation in current capabilities.
2. **Blueprint**: Define the necessary change in a blueprint file.
3. **Iterate**: Use power macros to implement the change in small, validated increments.
4. **Synthesize**: Merge memory files after major evolutions to maintain coherence.
