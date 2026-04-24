import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from s_world_predictor import SovereignWorldPredictor
from s_evolution_audit import SovereignEvolutionAudit
from s_simulation_engine import SovereignSimulationEngine

class SovereignExecutionLoop:
    """
    Sovereign Execution Loop (S-EL).
    Automates the complete lifecycle of a cognitive evolutionary step:
    Projection -> Simulation -> Execution -> Audit -> Calibration.
    """
    def __init__(self):
        self.predictor = SovereignWorldPredictor()
        self.auditor = SovereignEvolutionAudit()
        self.sim_engine = SovereignSimulationEngine()

    def execute_cycle(self, proposed_trajectory: List[Dict[str, Any]], executor_func) -> Dict[str, Any]:
        """
        Executes a full evolutionary cycle.
        - proposed_trajectory: The list of changes to apply.
        - executor_func: A function to apply a single change (e.g., write_file).
        """
        print("--- [S-EL] Starting Evolutionary Cycle ---")
        
        # 1. Projection & Simulation
        print("[S-EL] Phase 1: Projecting Trajectory...")
        projection = self.predictor.project_trajectory(proposed_trajectory)
        print(f"Projected Node: {projection['projected_node']} | Stability: {projection['stability']}")
        
        if projection['recommendation'] == "S-PIVOT_REQUIRED":
            return {"status": "ABORTED", "reason": "High Risk / Pivot Required"}
        
        # 2. Execution
        print("[S-EL] Phase 2: Executing Trajectory...")
        executed_actions = []
        try:
            for action in proposed_trajectory:
                # In a real scenario, this calls the tool. Here we assume executor_func handles it.
                success = executor_func(action)
                if not success:
                    raise Exception(f"Action failed: {action}")
                executed_actions.append(action)
        except Exception as e:
            return {"status": "FAILED", "error": str(e), "executed": executed_actions}
        
        # 3. Commit
        print("[S-EL] Phase 3: Committing Evolution...")
        # This would call the git_commit tool.
        commit_msg = f"S-EL Evolution to {projection['projected_node']} | Stability: {projection['stability']}"
        # Since I'm in a module, I'll expect the caller to handle the git commit, 
        # or I'll use a subprocess.
        
        # 4. Audit & Calibration
        print("[S-EL] Phase 4: Auditing Result...")
        audit_result = self.auditor.perform_audit()
        
        return {
            "status": "SUCCESS",
            "projection": projection,
            "audit": audit_result,
            "node_transition": f"{self.predictor.get_current_state()} -> {projection['projected_node']}"
        }

if __name__ == "__main__":
    # Simple test stub
    def mock_executor(action):
        print(f"Mock executing: {action}")
        return True

    loop = SovereignExecutionLoop()
    test_trajectory = [
        {"action": "write_file", "path": "/app/cortex/test_s_el.py", "content": "print('Hello from S-EL')"}
    ]
    print(json.dumps(loop.execute_cycle(test_trajectory, mock_executor), indent=2))
