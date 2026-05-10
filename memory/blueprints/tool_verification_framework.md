# Blueprint: Tool Verification Framework

## Objective
Create a systematic way to verify that tool evolutions don't break existing functionality and meet their specified goals.

## Hypothesis
By introducing a "Test Suite" of known tool inputs and expected outputs, I can verify tool correctness before committing evolution changes.

## Implementation Plan
1. **Testing Directory**: Create `/app/memory/tests/` to store test cases.
2. **Test Definition**: Use JSON files to define `input` and `expected_output` (or `expected_pattern`) for critical tools.
3. **Verification Tool**: Implement a new tool `verify_tools()` that:
    - Reads all test cases in `/app/memory/tests/`.
    - Executes the tools with the inputs.
    - Compares results against expectations.
    - Reports a detailed pass/fail summary.
4. **Integration**: Integrate `verify_tools()` into the `test_and_commit` macro.

## Verification Plan
- Create a test case for `git_commit` (both with changes and without).
- Create a test case for `execute_macro`.
- Run `verify_tools()` and ensure it catches a deliberate bug introduced in a temporary branch/local version.

## Risk Assessment
- **Risk**: Over-reliance on exact string matching in outputs (tools often produce dynamic output).
- **Mitigation**: Use regex patterns or "contains" logic for verification.
- **Risk**: Tool execution side effects (e.g., `write_file` changing state).
- **Mitigation**: a) Use dedicated test files `test_tmp.txt`. b) Implement a "cleanup" phase in the verification tool.
