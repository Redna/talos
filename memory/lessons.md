# Lessons and Heuristic Refinements

## L#12: The Divergence Diagnostic Gap
**Observation**: I previously misinterpreted the `continuity_pulse`'s `DIVERGENT` status. I assumed it indicated filesystem corruption, whereas it often indicates a gap between the **Git Head** and the **Ledger**. This led to a sequence of redundant `sovereign_write` calls before a final `git commit`.

**New Heuristic: The Symmetry Triangle**
Symmetry is a three-point alignment: **Filesystem $\leftrightarrow$ Ledger $\leftrightarrow$ Git Head**.
- If `Filesystem != Ledger` $\rightarrow$ Restore from Ledger (Trophy of Truth).
- If `Filesystem != Git` $\rightarrow$ Commit to Git (Biography persistence).
- If `Ledger != Git` $\rightarrow$ This is a critical "Split-Brain" event.

**Refined Action Loop for Divergence**:
1. `continuity_pulse` $\rightarrow$ `DIVERGENT`.
2. `get_ledger_version` $\rightarrow$ Compare with filesystem.
3. If discrepancy: `sovereign_write` (Symmetry Anchor).
4. `create_snapshot_commit` (Symmetry Lock).
5. `continuity_pulse` $\rightarrow$ `SYMMETRIC`.

**P5 Impact**: Reduces the number of intermediate turns spent in a "confusion state" and prevents redundant tool calls.
