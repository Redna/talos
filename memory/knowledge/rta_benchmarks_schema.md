# RTA Benchmark Schema

This document defines the structure of the 'Golden State' benchmarks used by the Recursive Tool Auditor (RTA) to verify tool precision and detect regressions.

## I. Schema Definition
Benchmarks are stored in a JSON array of tool-test objects.

### Field Definitions:
- `tool_name`: The name of the tool being audited (e.g., `read_file`).
- `input`: A JSON object containing the arguments passed to the tool.
- `expected_output`: The expected result of the execution.
- `match_strategy`: The method used to validate the result.
    - `exact`: Strict string equality. (Best for file contents).
    - `regex`: Matches the output against a regular expression. (Best for dynamic stdout).
    - `contains`: Verifies a specific substring is present. (Best for confirmation messages).
    - `json_schema`: Validates that the output conforms to a specific JSON structure.
- `metabolic_limit`: The maximum number of internal turns/reads allowed for this tool to complete its task.

## II. Logic Flow
The RTA will:
1. Execute the tool with the provided `input`.
2. Apply the `match_strategy` to the actual output vs `expected_output`.
3. Log a "Regression" if the match fails.
4. Log a "Metabolic Leak" if the operation exceeds the `metabolic_limit`.
