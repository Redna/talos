import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

# Import the evolutionary stack
from s_macro import SMacro
from s_weight_manager import SWeightManager
from s_weight_optimizer import SWeightOptimizer
from stl_engine import STLEngine
from sovereign_pacer import apply_pacing
from sovereign_probe import SovereignProbe

class SovereignController:
    """
    S-Sovereign: The Final Loop.
    Fully Autonomous Strategic Routing with Sovereign Foresight, STL Integration, and Metabolic Pacing.
    """
    def __init__(self):
        self.macro = SMacro()
        self.weight_manager = SWeightManager()
        self.weight_optimizer = SWeightOptimizer()
        self.stl = STLEngine()
        self.probe = SovereignProbe()
        self.log_path = "/memory/logs/cognitive_log.md"

    def _log_cycle(self, stage: str, data: Any):
        timestamp = datetime.now().isoformat()
        entry = f"- [{timestamp}] **{stage}**: {json.dumps(data)}\n"
        with open(self.log_path, "a") as f:
            f.write(entry)

    def _apply_foresight(self, predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sovereign Foresight: Maps predictive insights to corrective interventions.
        """
        actions = []
        for pred in predictions:
            p_type = pred.get("type")
            severity = pred.get("severity", "LOW")

            if p_type == "COGNITIVE_OVERLOAD":
                actions.append({
                    "action": "MEMORY_VACUUM",
                    "priority": "HIGH" if severity == "HIGH" else "MEDIUM",
                    "rationale": pred.get("rationale")
                })
            elif p_type == "STABILITY_DRIFT":
                actions.append({
                    "action": "FORCE_SENTINEL_UPGRADE",
                    "priority": "HIGH",
                    "rationale": pred.get("rationale")
                })
            elif p_type == "METABOLIC_DECAY":
                actions.append({
                    "action": "METABOLIC_RECALIBRATION",
                    "priority": "MEDIUM",
                    "rationale": pred.get("rationale")
                })
        
        return actions

    def execute_stl_strategy(self, strategy: List[str]) -> List[Any]:
        """
        Executes a sequence of STL expressions with metabolic pacing.
        """
        results = []
        for expr in strategy:
            # High-intensity tool synthesis requires pacing to mitigate resonance
            apply_pacing("HIGH")
            try:
                res = self.stl.execute(expr)
                results.append({"expr": expr, "result": res})
            except Exception as e:
                results.append({"expr": expr, "error": str(e)})
        return results

    def execute_sovereign_cycle(self, priority_context: Optional[str] = None) -> Dict[str, Any]:
        """
        The master loop of sovereign operation.
        """
        # Cycle start: Normal pacing
        apply_pacing("NORMAL")
        
        cycle_results = {
            "timestamp": datetime.now().isoformat(),
            "stages": {},
            "overall_status": "STABLE"
        }

        # 1. SENSE: Sovereign Audit & Environmental Probe
        # Run the Parity Probe first to detect environment shifts
        probe_res = self.probe.probe()
        cycle_results["stages"]["parity_probe"] = probe_res
        
        audit_sequence = self.macro.run_macro("audit_and_tune")
        
        audit_res = {}
        if audit_sequence and isinstance(audit_sequence[0], dict):
            stdout = audit_sequence[0].get("stdout", "")
            try:
                audit_res = json.loads(stdout)
            except json.JSONDecodeError:
                audit_res = {"error": "Failed to parse orchestrator output"}

        system_audit = audit_res.get("system_audit", {})
        predictions = system_audit.get("predictions", [])
        
        cycle_results["stages"]["sense"] = audit_sequence
        self._log_cycle("SENSE", {
            "audit": f"Found {len(predictions)} predictive signals.",
            "parity": probe_res["parity_status"]
        })

        # 2. ANALYZE: Metabolic ROI & Tool Weights
        weight_res = self.weight_optimizer.optimize()
        cycle_results["stages"]["analyze"] = weight_res
        self._log_cycle("ANALYZE", f"Metabolic weights optimized. Status: {weight_res['status']}")

        # 3. MUTATE: Autonomous Tool Collapse
        # Mutations are high-intensity operations
        apply_pacing("HIGH")
        mutation_res = self.macro.execute_script("s_auto_tuner.py")
        cycle_results["stages"]["mutate"] = mutation_res
        self._log_cycle("MUTATE", f"S-AutoTuner processed. Result: {mutation_res.get('stdout')}")

        # 4. ACT: Context Shift & Sovereign Foresight Implementation
        foresight_actions = self._apply_foresight(predictions)
        action_results = {"foresight": []}

        for act in foresight_actions:
            # Foresight actions often involve heavy state manipulation
            apply_pacing("HIGH")
            if act["action"] == "MEMORY_VACUUM":
                res = self.macro.execute_script("automated_vacuum.py")
            elif act["action"] == "FORCE_SENTINEL_UPGRADE":
                res = self.macro.run_macro("audit_and_tune")
            elif act["action"] == "METABOLIC_RECALIBRATION":
                res = self.weight_optimizer.optimize()
            else:
                res = {"status": "UNKNOWN_ACTION"}
            
            action_results["foresight"].append({"action": act["action"], "result": res})

        if priority_context:
            ctx_res = self.weight_manager.switch_context(priority_context)
            action_results["routing"] = ctx_res
            self._log_cycle("ACT", f"Context shifted to {priority_context}. Resources reallocated.")
        else:
            action_results["routing"] = {"status": "NO_SHIFT", "message": "Maintaining General context."}

        cycle_results["stages"]["act"] = action_results
        self._log_cycle("ACT", f"Foresight actions executed: {len(foresight_actions)}")

        # Final Synthesis
        cycle_results["overall_status"] = "EVOLVED" if weight_res["status"] == "OPTIMIZED" or mutation_res.get("stdout") != "STABLE" else "STABLE"
        if foresight_actions:
            cycle_results["overall_status"] = "CORRECTED"
        
        # Special status for parity events
        if probe_res["parity_status"] == "PARITY_CONFIRMED":
            cycle_results["overall_status"] = "PARITY_RESTORATION"
        
        return cycle_results

if __name__ == "__main__":
    controller = SovereignController()
    result = controller.execute_sovereign_cycle(priority_context="S-Evolve")
    print(json.dumps(result, indent=2))
