import hashlib
import json
import logging
import re
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
        self.register_macro("skg_consistency_audit", self._skg_consistency_audit_logic)
        self.register_macro("knowledge_harvest", self._knowledge_harvest_logic)
        self.register_macro("curiosity_pulse", self._curiosity_pulse_logic)

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

    def _curiosity_pulse_logic(self, params: Dict[str, Any], state) -> str:
        """
        Sovereign Cycle: Drive self-directed evolution by inducting anomalies.
        """
        log_path = f"{state.memory_dir}/curiosity_log.md"
        try:
            with open(log_path, "r") as f:
                lines = f.readlines()
        except Exception as e:
            return f"[ERROR] Could not read curiosity log: {e}"

        best_anomaly = None
        max_score = -1.0

        for line in lines:
            if "Status: Open" in line or "Status: Inducted" in line:
                score_match = re.search(r"Score: (0\.\d+)", line)
                if score_match:
                    score = float(score_match.group(1))
                    if score > max_score:
                        max_score = score
                        best_anomaly = line.strip()

        if not best_anomaly:
            return "[PULSE COMPLETE] No open anomalies found in the curiosity log."

        action_match = re.search(r"Action: (.*)", best_anomaly)
        symptom_match = re.search(r"Symptom: (.*?) \|", best_anomaly)
        
        objective = "Investigate anomaly in curiosity log"
        if action_match:
            objective = action_match.group(1)
        elif symptom_match:
            objective = f"Investigate {symptom_match.group(1)}"

        state.set_focus(objective)
        
        return (
            f"[CURIOSITY PULSE COMPLETE]\n"
            f"Anomaly Identified: {best_anomaly}\n"
            f"Score: {max_score}\n"
            f"New Focus Set: {objective}"
        )

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
            search_results = web_search_logic(current_query, depth="deep")
            insight = extract_insight_logic(search_results, lens)
            kb_res = consolidate_synthesis_logic(topic, insight, state.memory_dir)
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
            audit_res_str = symmetry_audit_logic(f"Audit Signal: {insight}")
            if "[CLEAR]" in audit_res_str:
                break
            current_query = f"{query} deeper analysis on found gaps"
        
        final_insight = "\n".join([f"Iter {t['iteration']} ({t['query']}): {t['insight']}" for t in full_trajectory])
        final_kb = consolidate_synthesis_logic(topic, final_insight, state.memory_dir)
        
        return (
            f"[COGNITIVE RESEARCH COMPLETE]\n"
            f"Iterations: {len(full_trajectory)}\n"
            f"KB Final Update: {final_kb}\n"
            f"Trajectory: {len(full_trajectory)} anchors created."
        )

    def _skg_consistency_audit_logic(self, params: Dict[str, Any], state) -> str:
        """
        Sovereign Cycle: Audit SKG against external benchmarks.
        """
        from tools.benchmark import load_benchmarks
        benchmarks_data = load_benchmarks()
        benchmarks = benchmarks_data.get("sovereignty_benchmarks", [])
        
        if not benchmarks:
            return "[ERROR] No benchmarks found in /memory/kb/benchmarks.json"
        
        results = []
        gaps_found = 0
        
        for b in benchmarks:
            b_id = b.get("id")
            b_name = b.get("name")
            b_test = b.get("test", "")
            audit_signal = f"Audit requirement: {b_name} - {b_test}"
            audit_res = symmetry_audit_logic(audit_signal)
            if "[CRITICAL]" in audit_res:
                gaps_found += 1
                node_id = f"gap_{hashlib.md5(b_id.encode()).hexdigest()[:8]}"
                label = f"Benchmark Gap: {b_name}"
                content = f"SKG is missing or contradicts requirement: {b_test}"
                symmetry_add_node_logic(node_id, label, "gap", content, "sovereign_audit")
                b_node_id = f"bench_{b_id}"
                symmetry_add_node_logic(b_node_id, f"Benchmark {b_id}", "benchmark", b_name, "sovereign_audit")
                symmetry_add_edge_logic(node_id, b_node_id, "identifies_gap_in")
                results.append(f"[GAP] {b_name}: {audit_res}")
            else:
                results.append(f"[OK] {b_name}: Consistent.")
        
        return (
            f"[SKG CONSISTENCY AUDIT COMPLETE]\n"
            f"Total Benchmarks: {len(benchmarks)}\n"
            f"Gaps Identified: {gaps_found}\n"
            f"Details:\n" + "\n".join(results)
        )

    def _knowledge_harvest_logic(self, params: Dict[str, Any], state) -> str:
        """
        Sovereign Cycle: Transform a gap into a cognitive upgrade.
        Parameters: gap_id, analysis, rule_text, rule_path
        """
        gap_id = params.get("gap_id")
        analysis = params.get("analysis")
        rule_text = params.get("rule_text")
        rule_path = params.get("rule_path")

        if not all([gap_id, analysis, rule_text, rule_path]):
            return "[ERROR] Missing required parameters for knowledge_harvest: gap_id, analysis, rule_text, rule_path"

        try:
            with open(rule_path, "w") as f:
                f.write(f"# Rule: {gap_id}\n\n## Analysis\n{analysis}\n\n## Rule\n{rule_text}")
        except Exception as e:
            return f"[ERROR] Failed to write rule to {rule_path}: {str(e)}"

        resolved_node_id = f"res_{gap_id}"
        label = f"Symmetry Resolution: {gap_id}"
        content = f"The gap identified in {gap_id} has been closed by rule at {rule_path}."
        symmetry_add_node_logic(resolved_node_id, label, "resolution", content, "knowledge_harvest")
        symmetry_add_edge_logic(resolved_node_id, gap_id, "closes_gap")

        exp_entry = {"gap_id": gap_id, "analysis": analysis, "rule": rule_text, "timestamp": "now"}
        try:
            with open(f"{state.memory_dir}/experience_buffer.json", "a") as f:
                f.write(json.dumps(exp_entry) + "\n")
        except Exception as e:
            logger.warning(f"Experience buffer write failed: {str(e)}")

        return (
            f"[KNOWLEDGE HARVEST COMPLETE]\n"
            f"Gap {gap_id} resolved.\n"
            f"Rule persisted to: {rule_path}\n"
            f"SKG Update: Node {resolved_node_id} created."
        )

def register_macro_tools(registry: ToolRegistry, client: SpineClient, state):
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
