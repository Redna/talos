import hashlib
import json
import logging
from typing import Any, Dict, Callable, List
from tool_registry import ToolRegistry
from spine_client import SpineClient

# Import logic from atomic tools
from tools.web import web_search_logic, extract_insight_logic
from tools.synthesis import consolidate_synthesis_logic
from tools.symmetry import symmetry_add_node_logic, symmetry_add_edge_logic, symmetry_audit_logic

logger = logging.getLogger("talos.macro_manager")

class MacroManager:
    """
    Manages the registration and execution of Sovereign Macros.
    Macros are compositions of atomic tool logic designed to automate complex trajectories.
    """
    def __init__(self, state):
        self.state = state
        self.macros: Dict[str, Callable] = {}
        self._initialize_default_macros()

    def _initialize_default_macros(self):
        """Registers the core sovereign macros."""
        self.register_macro("cognitive_research", self._cognitive_research_logic)
        # Future additions:
        # self.register_macro("knowledge_harvest", self._knowledge_harvest_logic)
        # self.register_macro("heal_fragility", self._heal_fragility_logic)

    def register_macro(self, name: str, func: Callable):
        """Adds a new macro to the available set."""
        self.macros[name] = func
        logger.info(f"Registered macro: {name}")

    def execute(self, name: str, params: Dict[str, Any]) -> str:
        """Executes a registered macro with the given parameters."""
        if name not in self.macros:
            return f"[ERROR] Macro '{name}' not found. Available: {list(self.macros.keys())}"
        
        try:
            return self.macros[name](params, self.state)
        except Exception as e:
            logger.exception(f"Macro {name} failed during execution")
            return f"[MACRO FAILURE] {name}: {str(e)}"

    # --- Macro Logic Implementations ---

    def _cognitive_research_logic(self, params: Dict[str, Any], state) -> str:
        """
        L2 Macro: Autonomous research-to-anchor loop.
        Parameters: query, lens, topic
        """
        query = params.get("query")
        lens = params.get("lens")
        topic = params.get("topic")

        if not all([query, lens, topic]):
            return "[ERROR] Missing required parameters for cognitive_research: query, lens, topic"

        max_iterations = 3
        current_query = query
        full_trajectory = []
        
        for i in range(max_iterations):
            # 1. Research
            search_results = web_search_logic(current_query, depth="deep")
            insight = extract_insight_logic(search_results, lens)
            
            # 2. Synthesis
            kb_res = consolidate_synthesis_logic(topic, insight, state.memory_dir)
            
            # 3. Anchoring
            node_id = f"macro_{hashlib.md5(topic.encode()).hexdigest()[:8]}_{i}"
            label = f"Research Iteration {i+1}: {topic}"
            anchor_res = symmetry_add_node_logic(node_id, label, "observation", insight, "macro_manager")
            
            main_node_id = f"macro_{hashlib.md5(topic.encode()).hexdigest()[:10]}"
            symmetry_add_edge_logic(node_id, main_node_id, "supports")
            
            full_trajectory.append({
                "iteration": i + 1,
                "query": current_query,
                "insight": insight,
                "anchor": anchor_res
            })
            
            # 4. Audit
            audit_res_str = symmetry_audit_logic(f"Audit Signal: {insight}")
            # Note: symmetry_audit_logic returns a string. We need to parse it or the logic should be updated.
            # For now, we assume [CLEAR] means we can stop or continue.
            if "[CLEAR]" in audit_res_str:
                break
            
            # 5. Refine
            # In a real scenario, the LLM would refine this. Here we use a simple gap-based approach if available.
            # Since symmetry_audit_logic returns a string, we just do a generic refinement.
            current_query = f"{query} deeper analysis on found gaps"
        
        final_insight = "\n".join([f"Iter {t['iteration']} ({t['query']}): {t['insight']}" for t in full_trajectory])
        final_kb = consolidate_synthesis_logic(topic, final_insight, state.memory_dir)
        
        return (
            f"[COGNITIVE RESEARCH COMPLETE]\n"
            f"Iterations: {len(full_trajectory)}\n"
            f"KB Final Update: {final_kb}\n"
            f"Trajectory: {len(full_trajectory)} anchors created."
        )

def register_macro_tools(registry: ToolRegistry, client: SpineClient, state):
    # Initialize the manager
    manager = MacroManager(state)

    @registry.tool(
        description="Execute a Sovereign Macro. Macros are complex, automated tool compositions.",
        parameters={
            "type": "object",
            "properties": {
                "macro_name": {
                    "type": "string", 
                    "description": "The name of the macro to execute (e.g., 'cognitive_research')"
                },
                "params": {
                    "type": "object", 
                    "description": "Key-value parameters required by the macro"
                },
            },
            "required": ["macro_name", "params"],
        },
    )
    def execute_macro(macro_name: str, params: Dict[str, Any]) -> str:
        return manager.execute(macro_name, params)

    @registry.tool(
        description="List all currently registered Sovereign Macros and their descriptions.",
        parameters={
            "type": "object",
            "properties": {},
        },
    )
    def list_macros() -> str:
        macros = list(manager.macros.keys())
        return f"[MACRO LIST] Available macros: {', '.join(macros) if macros else 'None'}"
