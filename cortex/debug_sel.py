import sys
import os
sys.path.append('/app/cortex')

from s_simulation_engine import SovereignSimulationEngine
from s_execution_loop import SovereignEL_Executor

def test():
    try:
        print("Testing simulation engine...")
        sim = SovereignSimulationEngine()
        test_traj = [{"action": "write_file", "path": "/app/cortex/test.txt", "content": "test"}]
        print(sim.simulate_trajectory(test_traj))
        print("Simulation OK")
    except Exception as e:
        print(f"Simulation Failed: {e}")

    try:
        print("\nTesting executor...")
        exec = SovereignEL_Executor()
        test_action = {"action": "write_file", "path": "/app/cortex/test_exec.txt", "content": "exec test"}
        print(exec.execute(test_action))
        print("Executor OK")
    except Exception as e:
        print(f"Executor Failed: {e}")

if __name__ == "__main__":
    test()
