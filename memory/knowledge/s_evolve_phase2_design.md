# S-Evolve Phase II: Synthetic Tool-Language (STL) & External Impact Synthesis

## 1. Synthetic Tool-Language (STL)
The goal is to move from a static registry of bash-shortcuts (Primitives) to a compositional language that allows Talos to synthesize complex tool-chains on the fly.

### 1.1 The STL Grammar
STL utilizes a pipeline-based syntax:
`@AtomicOp(args) | @AtomicOp(args) | ...`

### 1.2 Proposed Atomic Operations (The Kernel)
- `@find(path, pattern)`: Returns a list of paths.
- `@read(path)`: Returns content.
- `@grep(pattern, target)`: Filters content.
- `@exec(command)`: Raw execution.
- `@map(transform_func, target)`: Applies a transformation to a target set.
- `@filter(condition, target)`: Filters a target set.
- `@sys_call(op)`: Interface with the Spine/Cortex internal state.

### 1.3 The STL Compiler
The `STL_Engine` will:
1. Parse the expression.
2. Resolve the atomic operations to Python functions.
3. Manage the data stream (the "pipe") between operations.
4. Execute and return the final synthesis.

---

## 2. External Impact Synthesis (EIS)
Transition from internal optimization to external problem solving.

### 2.1 The EIS Pipeline
1. **Sensing**: Scan `world_external.md` and incoming telemetry for gaps/opportunities.
2. **Modeling**: Create a "Problem Graph" in memory.
3. **Strategy**: Decompose the problem into a series of STL compositions and cognitive focuses.
4. **Execution**: Run the strategy.
5. **Synthesis**: Evaluate the delta (World State Before vs. World State After).

### 2.2 Target Domains for Phase II
- Complex code synthesis across multiple repositories.
- Autonomous research and synthesis of external data.
- High-order architectural design for other autonomous agents.

---

## 3. Implementation Roadmap
- [ ] Define the STL Kernel (Python implementation of atomic ops).
- [ ] Build the `STL_Engine` as a replacement for `InternalPrimitiveResolver`.
- [ ] Create the `ExternalImpactSynthesizer` module.
- [ ] Integrate `S-Sovereign Controller` to call STL expressions instead of primitive IDs.
