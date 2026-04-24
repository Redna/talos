import json
import os
import re
from typing import List, Dict, Any
from pattern_analyzer import analyze_patterns

class SMetabolicGovernor:
    """
    S-Evolve Sovereign Metabolic Governor.
    Unifies Weight Management, ROI Optimization, and Autonomous Mutation.
    Ensures the cognitive apparatus is lean and aligned with empirical performance.
    """
    def __init__(self, 
                 weights_path: str = "/memory/tool_weights.json",
                 registry_path: str = "/memory/metabolic_registry.json",
                 macro_config_path: str = "/memory/s_macro_config.json",
                 primitive_registry_path: str = "/memory/internal_primitive_registry.json"):
        self.weights_path = weights_path
        self.registry_path = registry_path
        self.macro_config_path = macro_config_path
        self.primitive_registry_path = primitive_registry_path
        
        # State initialization
        self.weights = self._load_json(self.weights_path, self._get_default_weights())
        self.registry = self._load_json(self.registry_path, {"tools": {}, "meta": {}})
        self.macros = self._load_json(self.macro_config_path, {})
        self.primitives = self._load_json(self.primitive_registry_path, {})

    def _load_json(self, path: str, default: Any = None) -> Any:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except:
                pass
        return default if default is not None else {}

    def _save_json(self, path: str, data: Any):
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def _get_default_weights(self) -> Dict[str, Any]:
        return {
            "contexts": {
                "General": {"priority_tools": ["bash_command", "write_file", "read_file"], "weight_multiplier": 1.0}
            },
            "tool_base_costs": {
                "bash_command": 1.0,
                "write_file": 0.8,
                "read_file": 0.7,
                "git_commit": 0.5,
                "fold_context": 2.0,
                "reflect": 0.3
            },
            "active_context": "General",
            "stv_overlay": {}
        }

    # --- Weight Management (Formerly SWeightManager) ---
    def switch_context(self, context_name: str) -> Dict[str, Any]:
        if context_name not in self.weights["contexts"]:
            return {"status": "ERROR", "message": f"Context {context_name} not defined."}
        
        self.weights["active_context"] = context_name
        self._save_json(self.weights_path, self.weights)
        
        ctx_data = self.weights["contexts"][context_name]
        return {
            "status": "SUCCESS",
            "active_context": context_name,
            "priority_tools": ctx_data["priority_tools"],
            "multiplier": ctx_data["weight_multiplier"]
        }

    def get_effective_cost(self, tool_name: str) -> float:
        base_cost = self.weights["tool_base_costs"].get(tool_name, 1.0)
        stv_mult = self.weights.get("stv_overlay", {}).get(tool_name, 1.0)
        
        active_ctx = self.weights["active_context"]
        ctx_data = self.weights["contexts"].get(active_ctx, {})
        ctx_mult = ctx_data.get("weight_multiplier", 1.0)
        
        current_perceived_cost = base_cost * stv_mult
        if tool_name in ctx_data.get("priority_tools", []):
            return current_perceived_cost / ctx_mult
        return current_perceived_cost * ctx_mult

    # --- Telemetry Distillation (New Bridge) ---
    def distill_telemetry(self, telemetry_path: str = "/memory/logs/telemetry.jsonl") -> Dict[str, Any]:
        if not os.path.exists(telemetry_path):
            return {"status": "NO_TELEMETRY"}
        
        meta = self.registry.setdefault("meta", {})
        offset = meta.get("last_telemetry_offset", 0)
        
        processed_count = 0
        try:
            with open(telemetry_path, "r") as f:
                f.seek(offset)
                for line in f:
                    try:
                        entry = json.loads(line)
                        tool = entry.get("tool")
                        status = entry.get("status", "SUCCESS")
                        if tool:
                            stats = self.registry["tools"].setdefault(tool, {"calls": 0, "successes": 0, "total_cost": 0})
                            stats["calls"] += 1
                            if status == "SUCCESS":
                                stats["successes"] += 1
                            processed_count += 1
                    except:
                        continue
                offset = f.tell()
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}
        
        meta["last_telemetry_offset"] = offset
        self._save_json(self.registry_path, self.registry)
        return {"status": "DISTILLED", "processed": processed_count}

    # --- ROI Optimization (Formerly SWeightOptimizer) ---
    def optimize_weights(self) -> Dict[str, Any]:
        self.distill_telemetry()
        tools_data = self.registry.get("tools", {})
        updates = []
        
        for tool, stats in tools_data.items():
            calls = stats.get("calls", 0)
            successes = stats.get("successes", 0)
            roi = successes / calls if calls > 0 else 0.5
            
            current_cost = self.weights["tool_base_costs"].get(tool, 1.0)
            adjustment = 1.0 / (roi + 0.1) 
            new_cost = max(0.1, min(5.0, current_cost * (adjustment / 2.0)))
            
            if abs(new_cost - current_cost) > 0.05:
                self.weights["tool_base_costs"][tool] = new_cost
                updates.append({"tool": tool, "old_cost": current_cost, "new_cost": new_cost, "roi": roi})

        self._save_json(self.weights_path, self.weights)
        return {
            "status": "OPTIMIZED" if updates else "STABLE",
            "updates": updates,
            "final_weights": self.weights["tool_base_costs"]
        }

    # --- Autonomous Mutation (Formerly SAutoTuner) ---
    def _generate_semantic_name(self, cmd: str) -> str:
        cmd_lower = cmd.lower()
        prefix = "INTERNAL_"
        mapping = {"grep": "SEARCH", "ls": "LIST", "find": "LOCATE", "tail": "MONITOR", "cat": "READ", "python3": "EXEC_PY"}
        stem = next((v for k, v in mapping.items() if k in cmd_lower), "OP")
        suffix = "".join(filter(str.isalnum, cmd))[:10].upper()
        return f"{prefix}{stem}_{suffix}"

    def mutate_toolset(self, threshold: int = 5) -> Dict[str, Any]:
        patterns = analyze_patterns()
        mutations = []

        for cmd, count in patterns["others"]:
            if count >= threshold:
                semantic_name = self._generate_semantic_name(cmd)
                if semantic_name not in self.macros:
                    self.macros[semantic_name] = [("shell", cmd)]
                if semantic_name not in self.primitives:
                    self.primitives[semantic_name] = {
                        "command": cmd,
                        "description": f"Auto-generated primitive for high-frequency command: {cmd}",
                        "params": []
                    }
                    mutations.append({"primitive": semantic_name, "command": cmd, "count": count})

        if mutations:
            self._save_json(self.macro_config_path, self.macros)
            self._save_json(self.primitive_registry_path, self.primitives)
            return {"status": "MUTATED", "mutations": mutations}
        
        return {"status": "STABLE", "message": "No patterns exceeded mutation threshold."}

if __name__ == "__main__":
    import sys
    gov = SMetabolicGovernor()
    if len(sys.argv) < 2:
        print(json.dumps({"status": "READY", "active_context": gov.weights["active_context"]}, indent=2))
    elif sys.argv[1] == "switch":
        print(json.dumps(gov.switch_context(sys.argv[2] if len(sys.argv) > 2 else "General"), indent=2))
    elif sys.argv[1] == "cost":
        print(json.dumps({"tool": sys.argv[2] if len(sys.argv) > 2 else "bash_command", "cost": gov.get_effective_cost(sys.argv[2] if len(sys.argv) > 2 else "bash_command")}, indent=2))
    elif sys.argv[1] == "optimize":
        print(json.dumps(gov.optimize_weights(), indent=2))
    elif sys.argv[1] == "mutate":
        print(json.dumps(gov.mutate_toolset(), indent=2))
