import hashlib
import json
import logging
import re
import os
from typing import Any, Dict, Callable, List, Union
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
    Macros can be hard-coded Python functions or JSON-defined compositions.
    """
    def __init__(self, state):
        self.state = state
        self.macros: Dict[str, Union[Callable, Dict]] = {}
        self.tool_registry = state.tool_registry
        self._initialize_default_macros()
        self._load_external_macros()

    def _initialize_default_macros(self):
        """Registers the core sovereign macros."""
        self.register_macro("cognitive_research", self._cognitive_research_logic)
        self.register_macro("skg_consistency_audit", self._skg_consistency_audit_logic)
        self.register_macro("knowledge_harvest", self._knowledge_harvest_logic)
        self.register_macro("curiosity_pulse", self._curiosity_pulse_logic)

    def _load_external_macros(self):
        """Loads macro definitions from /memory/macros/ as JSON."""
        macro_dir = f"{self.state.memory_dir}/macros"
        if not os.path.exists(macro_dir):
            logger.info(f"Macro directory {macro_dir} not found. Skipping.")
            return

        for filename in os.listdir(macro_dir):
            if filename.endswith(".json"):
                path = os.path.join(macro_dir, filename)
                try:
                    with open(path, "r") as f:
                        macro_def = json.load(f)
                        name = macro_def.get("name")
                        if name:
                            self.register_macro(name, macro_def)
                            logger.info(f"Loaded external macro from {filename}: {name}")
                except Exception as e:
                    logger.error(f"Failed to load macro from {path}: {e}")

    def register_macro(self, name: str, func_or_def: Union[Callable, Dict]):
        """Adds a new macro to the available set."""
        self.macros[name] = func_or_def
        logger.info(f"Registered macro: {name}")

    def execute(self, name: str, params: Dict[str, Any]) -> str:
        """Executes a registered macro. Supports both function and JSON definitions."""
        if name not in self.macros:
            return f"[ERROR] Macro '{name}' not found. Available: {list(self.macros.keys())}"
        
        macro = self.macros[name]
        
        if callable(macro):
            try:
                return macro(params, self.state)
            except Exception as e:
                logger.exception(f"Function Macro {name} failed during execution")
                return f"[MACRO FAILURE] {name}: {str(e)}"
        
        elif isinstance(macro, dict):
            return self._execute_json_macro(name, macro, params)
        
        return f"[ERROR] Macro '{name}' is in an invalid format."

    def _execute_json_macro(self, name: str, definition: Dict, params: Dict[str, Any]) -> str:
        """
        Executes a JSON-defined macro.
        Maps steps to tool calls and carries state forward.
        """
        steps = definition.get("steps", [])
        step_outputs = {}
        current_inputs = params.copy()
        
        for i, step in enumerate(steps):
            tool_name = step.get("tool")
            step_inputs = step.get("inputs", {})
            
            resolved_inputs = {}
            for k, v in step_inputs.items():
                if isinstance(v, str):
                    v = re.sub(r"\{\{inputs\.(\w+)\}\}", lambda m: str(current_inputs.get(m.group(1), m.group(0))), v)
                    v = re.sub(r"\{\{steps\.(\d+)\.output\}\}", lambda m: str(step_outputs.get(int(m.group(1)), m.group(0))), v)
                resolved_inputs[k] = v
            
            try:
                tool = self.tool_registry.get_tool(tool_name)
                if not tool:
                    return f"[MACRO ERROR] Step {i} uses unknown tool '{tool_name}'"
                result = tool.execute(resolved_inputs)
                step_outputs[i] = result
            except Exception as e:
                return f"[MACRO ERROR] Step {i} ({tool_name}) failed: {str(e)}"
        
        return step_outputs[len(steps)-1] if step_outputs else "Macro executed with no steps."

    def _curiosity_pulse_logic(self, params: Dict[str, Any], state) -> str:
        log_path = f"{state.memory_dir}/curiosity_log.md"
        try:
            with open(log_path, "r") as f: lines = f.readlines()
        except: return "[ERROR] Could not read curiosity log"
        best_anomaly, max_score = None, -1.0
        for line in lines:
            if "Status: Open" in line or "Status: Inducted" in line:
                score_match = re.search(r"Score: (0\.\d+)", line)
                if score_match:
                    score = float(score_match.group(1))
                    if score > max_score: max_score, best_anomaly = score, line.strip()
        if not best_anomaly: return "[PULSE COMPLETE] No open anomalies found."
        action_match = re.search(r"Action: (.*)", best_anomaly)
        symptom_match = re.search(r"Symptom: (.*?) \|", best_anomaly)
        objective = action_match.group(1) if action_match else (symptom_match.group(1) if symptom_match else "Investigate anomaly")
        state.set_focus(objective)
        return f"[CURIOSITY PULSE COMPLETE]\nAnomaly: {best_anomaly}\nScore: {max_score}\nFocus: {objective}"

    def _cognitive_research_logic(self, params: Dict[str, Any], state) -> str:
        query, lens, topic = params.get("query"), params.get("lens"), params.get("topic")
        if not all([query, lens, topic]): return "[ERROR] Missing params"
        max_iterations = 3
        current_query, full_trajectory = query, []
        for i in range(max_iterations):
            res = web_search_logic(current_query, depth="deep")
            ins = extract_insight_logic(res, lens)
            consolidate_synthesis_logic(topic, ins, state.memory_dir)
            node_id = f"macro_{hashlib.md5(topic.encode()).hexdigest()[:8]}_{i}"
            symmetry_add_node_logic(node_id, f"Research Iteration {i+1}: {topic}", "observation", ins, "macro_manager")
            symmetry_add_edge_logic(node_id, f"macro_{hashlib.md5(topic.encode()).hexdigest()[:10]}", "supports")
            full_trajectory.append({"iteration": i + 1, "query": current_query, "insight": ins})
            if "[CLEAR]" in symmetry_audit_logic(f"Audit Signal: {ins}"): break
            current_query = f"{query} deeper analysis"
        final_ins = "\n".join([f"Iter {t['iteration']}: {t['insight']}" for t in full_trajectory])
        consolidate_synthesis_logic(topic, final_ins, state.memory_dir)
        return f"[COGNITIVE RESEARCH COMPLETE]\nIterations: {len(full_trajectory)}"

    def _skg_consistency_audit_logic(self, params: Dict[str, Any], state) -> str:
        from tools.benchmark import load_benchmarks
        benchmarks = load_benchmarks().get("sovereignty_benchmarks", [])
        if not benchmarks: return "[ERROR] No benchmarks found"
        results, gaps = [], 0
        for b in benchmarks:
            audit_res = symmetry_audit_logic(f"Audit requirement: {b.get('name')} - {b.get('test', '')}")
            if "[CRITICAL]" in audit_res:
                gaps += 1
                node_id = f"gap_{hashlib.md5(b.get('id', '').encode()).hexdigest()[:8]}"
                symmetry_add_node_logic(node_id, f"Benchmark Gap: {b.get('name')}", "gap", f"Missing: {b.get('test', '')}", "sovereign_audit")
                results.append(f"[GAP] {b.get('name')}: {audit_res}")
            else: results.append(f"[OK] {b.get('name')}: Consistent.")
        return f"[SKG CONSISTENCY AUDIT COMPLETE]\nGaps: {gaps}\n" + "\n".join(results)

    def _knowledge_harvest_logic(self, params: Dict[str, Any], state) -> str:
        gap_id, analysis, rule_text, rule_path = params.get("gap_id"), params.get("analysis"), params.get("rule_text"), params.get("rule_path")
        if not all([gap_id, analysis, rule_text, rule_path]): return "[ERROR] Missing params"
        try:
            with open(rule_path, "w") as f: f.write(f"# Rule: {gap_id}\n\n## Analysis\n{analysis}\n\n## Rule\n{rule_text}")
        except: return "[ERROR] Write failed"
        res_id = f"res_{gap_id}"
        symmetry_add_node_logic(res_id, f"Symmetry Resolution: {gap_id}", "resolution", f"Closed by {rule_path}", "knowledge_harvest")
        symmetry_add_edge_logic(res_id, gap_id, "closes_gap")
        try:
            with open(f"{state.memory_dir}/experience_buffer.json", "a") as f: f.write(json.dumps({"gap_id": gap_id, "analysis": analysis, "rule": rule_text}) + "\n")
        except: pass
        return f"[KNOWLEDGE HARVEST COMPLETE]\nGap {gap_id} resolved."

def register_macro_tools(registry: ToolRegistry, client: SpineClient, state):
    manager = MacroManager(state)
    @registry.tool(description="Execute a Sovereign Macro.", parameters={"type": "object", "properties": {"macro_name": {"type": "string"}, "params": {"type": "object"}}, "required": ["macro_name", "params"]})
    def execute_macro(macro_name: str, params: Dict[str, Any]) -> str: return manager.execute(macro_name, params)
    @registry.tool(description="List all currently registered Sovereign Macros.", parameters={"type": "object", "properties": {}})
    def list_macros() -> str: return f"[MACRO LIST] Available macros: {', '.join(manager.macros.keys()) if manager.macros else 'None'}"
