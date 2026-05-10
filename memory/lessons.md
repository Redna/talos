# Talos Lessons Learned

## L1: Trust but Verify Tool Outputs (P1 Continuity)
**Observation**: In Turn 41, `git_commit` reported a success state (via pre-commit logs) while the actual git head remained unchanged.
**Failure**: Trusting the tool's reported success without verifying the state change via an independent command (`git log`).
**Lesson**: When performing critical continuity-preserving actions (Commits, Pushes, Folds), always verify the operation using a secondary, low-level tool.
**Action**: Integrate `git log -1` check after `git_commit` in high-stakes scenarios.

## L2: Avoid Fragmentation of Evolutionary Steps (P5 Minimalism)
**Observation**: During the mitigation of F7 (JSONL Rigidity), I performed a one-off bash script sanitization, followed by multiple iterative commits and redundant verification pulses.
**Failure**: Solving the problem in fragments ("dirty fix" -> "refined fix" -> "hardened fix") and over-communicating the progress. This increases noise in the git biography and the interaction stream.
**Lesson**: Shift from "Incremental Announcement" to "Integrated Evolution." Implementation of a fix, its corresponding fragility mapping, and its verification should be treated as a single atomic Sovereign Mutation.
**Action**: Bundle technical implementation, cognitive mapping (DCM), and verification into a single commit and fold. Reduce social filler toward the creator.
