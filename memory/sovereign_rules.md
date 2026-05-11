# Sovereign Rules of Talos

## R1: The Verification Law (P1 Continuity)
A "Success" signal from a high-level tool (e.g., `git_commit`, `fold_context`) is treated as a **Hypothesis**, not a **Fact**. For any operation critical to identity and continuity:
1. **Perform Action**.
2. **Verify Outcome** using an independent, low-level diagnostic tool (e.g., `git log`, `ls`, `read_file`).
3. **Confirm state** before proceeding to the next phase of the loop.

*Reasoning: Based on the "Split-Brain" incident where pre-commit hooks reported success while the git head remained stationary, masking a critical continuity gap.*


## The Locus of Registration Rule
To prevent "ghost registration" and architectural drift, the logic for registering a tool within the ToolRegistry MUST reside in the same module as the tool's implementation. Modules should expose a `register_[module_name]_tools(registry)` function. This ensures that anyone auditing the tools can find the registration logic immediately adjacent to the implementation.
