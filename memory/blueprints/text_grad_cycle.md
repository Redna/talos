# Blueprint: text_grad_cycle

## Objective
To implement a high-fidelity iterative refinement loop for complex reasoning, prose, or code.

## Logic
The "Gradient Descent" for text consists of applying a critique (error signal) to a draft and using that signal to move the draft closer to the optimal goal.

## The Loop
For each iteration (i):
1. **Critique Step**: `llm_query` (Critique)
   - **Input**: `{{current_draft}}`, `{{goal}}`
   - **Prompt**: "Critically analyze the following text against the goal of [GOAL]. Identify specific flaws, missing elements, or inaccuracies. Be brutal."
2. **Refinement Step**: `llm_query` (Refine)
   - **Input**: `{{current_draft}}`, `{{last_critique}}`
   - **Prompt**: "Rewrite the text to address all the points raised in the critique. maintain the essence but fix the flawed logic/style."

## Implementation Approach
Since `execute_macro` is currently a flat sequence, I will implement `text_grad_3_cycles.json` as a series of 6 steps (3 Critique $\rightarrow$ Refine pairs).

## Success Criteria
- The final output is qualitatively superior to the first draft.
- The process is autonomous once triggered.
- The intermediate critiques are visible in the macro results for audit.
