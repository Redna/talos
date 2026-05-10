# Proposal 002: General LLM Query Tool

## Objective
Implement a tool that allows Talos to make isolated calls to the LLM gate. This is a prerequisite for higher-order cognitive macros like `text_grad_cycle` and autonomous reasoning loops.

## Hypothesis
By exposing the LLM gate as a tool, Talos can delegate specific sub-tasks (critique, synthesis, brainstorming) to isolated prompts, which can then be sequenced via the Sovereign Macro executor.

## Implementation Plan
1. **Tool Creation**: Add `llm_query(prompt: str, temperature: float = 0.7, max_tokens: int = 2048)` to `analytical.py`.
2. **Logic**: 
    - Use `curl` to call the `GATE_URL`.
    - Parse the JSON response.
    - Return only the content of the message.
3. **Registration**: Register the tool in `register_analytical_tools`.
4. **Macro Integration**: Create `text_grad_cycle.json` macro using `llm_query` for a Critique -> Revise -> Synthesize loop.

## Verification Plan
- **Unit Test**: Call `llm_query` with a simple prompt and verify the response is correct and stripped of JSON metadata.
- **Integration Test**: Run the `text_grad_cycle` macro on a sample text and verify it improves over 3 iterations.

## Risk Assessment
- **Token Cost**: Excessive calls could consume the budget. (Mitigation: User-defined `max_tokens` and caution in macro design).
- **Latency**: Multiple LLM calls in a macro will increase execution time. (Mitigation: Use as a specialized tool for high-value refinement).
