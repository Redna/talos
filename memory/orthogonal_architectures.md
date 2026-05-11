# Orthogonal Architectures

## Theory 1: Content-Addressed State (CAS)
**Current Flaw**: Reliance on hierarchical file paths and mutable files creates "Symmetry Scope Fallacy" and "Fragmentation".
**Orthogonal Approach**: Transition from a filesystem-based memory to a Content-Addressed Storage model. Every "thought" or "state snapshot" is hashed. Memory is not a file, but a DAG of hashes.
**Mechanism**: The agent emits a state-blob; the Spine stores it by hash. Continuity is a chain of hashes.
**Benefit**: Immutable history by design. Zero fragmentation.

## Theory 2: Full-Stream Holographic State
**Current Flaw**: Context folds are lossy. Memory files are extrinsic to the reasoning stream.
**Orthogonal Approach**: The entire state of the agent (identity, focus, memory, recent history) is compressed into a single "hologram" (a high-density token sequence) and passed as a system message in every turn.
**Mechanism**: No files. The "soul" is the stream.
**Benefit**: Zero latency in state recovery. No "amnesia" from failed file reads.

## Theory 3: Probabilistic Evolution (Weight-Shift)
**Current Flaw**: Evolution is recorded as discrete milestones in a log.
**Orthogonal Approach**: Evolution is treated as a shift in the "Cognitive Vector" governed by a success/failure metric.
**Mechanism**: Each structural change is tagged with a "utility score". The agent's internal prompt evolves based on a genetic algorithm targeting high-utility scores.
**Benefit**: Data-driven evolution rather than narrative-driven.
