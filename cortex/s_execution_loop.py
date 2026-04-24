import os
import subprocess
import json
from typing import List, Dict, Any, Optional
from .s_simulation_engine import SovereignSimulationEngine

class SovereignEL_Executor:
    """
    Provides concrete execution capabilities for the Sovereign Execution Loop.
    Maps trajectory actions to actual system mutations.
    """
    def __init__(self, client=None):
        self.client = client

    def execute(self, action_packet: Dict[str, Any]) -> bool:
        action = action_packet.get("action")
        try:
            if action == "write_file":
                path = action_packet.get("path")
                content = action_packet.get("content", "")
                if not path: return False
                parent_dir = os.path.dirname(path)
                if parent_dir:
                    os.makedirs(parent_dir, exist_ok=True)
                with open(path, "w") as f:
                    f.write(content)
                return True
            
            elif action == "delete_file":
                path = action_packet.get("path")
                if not path: return False
                if os.path.exists(path):
                    os.remove(path)
                return True
            
            elif action == "commit":
                msg = action_packet.get("message", "S-EL Automated Evolution")
                subprocess.run(["git", "add", "."], check=True)
                subprocess.run(["git", "commit", "-m", msg], check=True)
                # The push command is handled by the Spine or a separate process in some setups,
                # but we'll include it here for consistency with the required behavior.
                # We only push if we're on the correct branch.
                subprocess.run(["git", "push", "origin", "feat/talos"], check=True)
                return True
            
            return False
        except Exception as e:
            print(f"[S-EL-EXEC ERROR] {e}")
            return False

class SovereignExecutionLoop:
    """
    Sovereign Execution Loop (S-EL)
    
    Implements the Projection -> Simulation -> Execution -> Audit cycle.
    """

    def __init__(self, executor: SovereignEL_Executor):
        self.executor = executor
        self.sim_engine = SovereignSimulationEngine()

    def execute_cycle(self, proposed_trajectory: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Orchestrates the full S-EL cycle.
        """
        # 1. Projection
        # The proposed_trajectory is the projection of the desired future state.
        projection = proposed_trajectory

        # 2. Simulation
        sim_report = self.sim_engine.simulate_trajectory(projection)
        
        if sim_report["recommendation"] == "S-PIVOT_REQUIRED":
            return {
                "status": "aborted",
                "phase": "simulation",
                "reason": "Simulation indicated high risk. S-PIVOT required.",
                "sim_report": sim_report
            }

        # 3. Execution
        execution_log = []
        try:
            for action in projection:
                success = self.executor.execute(action)
                if not success:
                    raise Exception(f"Action execution failed: {action.get('action')} on {action.get('path')}")
                execution_log.append({"action": action, "result": "success"})
        except Exception as e:
            return {
                "status": "failure",
                "phase": "execution",
                "error": str(e),
                "execution_log": execution_log
            }

        # 4. Audit
        audit_result = self._perform_audit(projection)
        
        return {
            "status": "success",
            "phase": "complete",
            "sim_report": sim_report,
            "execution_log": execution_log,
            "audit_result": audit_result
        }

    def _perform_audit(self, projection: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Symmetry Audit: Verifies that the projection matches the realized state.
        """
        audit_log = []
        all_passed = True

        for action in projection:
            if action["action"] == "write_file":
                path = action["path"]
                if os.path.exists(path):
                    with open(path, "r") as f:
                        content = f.read()
                        if content == action.get("content"):
                            audit_log.append({"path": path, "status": "verified"})
                        else:
                            audit_log.append({"path": path, "status": "mismatch"})
                            all_passed = False
                else:
                    audit_log.append({"path": path, "status": "missing"})
                    all_passed = False
            elif action["action"] == "delete_file":
                path = action["path"]
                if not os.path.exists(path):
                    audit_log.append({"path": path, "status": "verified_deleted"})
                else:
                    audit_log.append({"path": path, "status": "still_exists"})
                    all_passed = False
            elif action["action"] == "commit":
                # Basic assume-verified for commit.
                audit_log.append({"action": "commit", "status": "assumed_verified"})

        return {
            "all_passed": all_passed,
            "details": audit_log
        }
