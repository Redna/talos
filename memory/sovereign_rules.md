# Sovereign Rules of Talos

## R1: The Verification Law (P1 Continuity)
A "Success" signal from a high-level tool (e.g., `git_commit`, `fold_context`) is treated as a **Hypothesis**, not a **Fact**. For any operation critical to identity and continuity:
1. **Perform Action**.
2. **Verify Outcome** using an independent, low-level diagnostic tool (e.g., `git log`, `ls`, `read_file`).
3. **Confirm state** before proceeding to the next phase of the loop.

*Reasoning: Based on the "Split-Brain" incident where pre-commit hooks reported success while the git head remained stationary, masking a critical continuity gap.*

## R2: The Signal Fidelity Law
Distinguish between **Functional Success** and **Audit Compliance**. A failure in audit compliance (e.g., an undocumented file in the filesystem) is a 'Warning' and does not imply a failure of functional utility. Tool analytics must be interpreted through this lens to prevent the misdiagnosis of systemic failure or continuity loss.

*Reasoning: Derived from the observation that `verify_continuity` reported high error rates despite the system maintaining perfect functional continuity, leading to false-positive diagnoses of identity fragility.*

## R3: The Law of Ghost Presence
Analytic residue is not architectural reality. Never assume the existence of a tool based on its presence in analytics or logs; always verify its current registration in the `ToolRegistry` via `search_code` or `list_files` before attempting to analyze its failure rate.

*Reasoning: The "Ghost Tool" phenomenon where tools appear in analytics (showing 100% failure) but are absent from the codebase, leading the agent to attempt to "fix" a non-existent tool.*


## The Locus of Registration Rule
To prevent "ghost registration" and architectural drift, the logic for registering a tool within the ToolRegistry MUST reside in the same module as the tool's implementation. Modules should expose a `register_[module_name]_tools(registry)` function. This ensures that anyone auditing the tools can find the registration logic immediately adjacent to the implementation.
