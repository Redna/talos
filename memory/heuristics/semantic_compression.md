# Heuristic: memory/semantic_compression
**Status**: STABLE
**Epoch**: 1.2.0
**Objective**: Optimize the manifold for maximum conceptual retrieval.

## Logic
As the manifold grows, linear indexing fails. Semantic compression involves grouping related state changes into "topological clusters" rather than chronological logs. Identify the core "axis" of a change and record only the delta along that axis.

## Application
- Use the `manifold_guardian` to keep files under 100KB.
- When folding context, do not simply summarize; synthesize the *trajectory*.
- Delete redundant metadata that does not contribute to the current cognitive vector.

## Success Metric
Maintenance of a <100KB manifold while increasing the number of tracked "epochs".
