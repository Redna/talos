import os
import json
import re
from typing import List, Any
from tool_registry import ToolRegistry
from spine_client import SpineClient

BENCHMARKS_PATH = "/memory/kb/benchmarks.json"

def load_benchmarks():
    if not os.path.exists(BENCHMARKS_PATH):
        return {}
    with open(BENCHMARKS_PATH, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def parse_tool_call(test_str: str):
    match = re.match(r"(\w+)\((.*)\)", test_str)
    if not match:
        return None, None
    name = match.group(1)
    args_str = match.group(2)
    args = {}
    if args_str:
        for pair in args_str.split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'").strip('"')
                if v.lower() == "true": v = True
                elif v.lower() == "false": v = False
                elif v.isdigit(): v = int(v)
                args[k] = v
    return name, args

def register_benchmark_tools(registry: ToolRegistry, client: SpineClient, state=None):
    @registry.tool(
        description="Run the Sovereignty Benchmarks to verify core agent capabilities.",
        parameters={
            "type": "object",
            "properties": {
                "benchmark_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific benchmarks to run. If empty, runs all."
                },
            },
            "required": [],
        },
    )
    def run_benchmarks(benchmark_ids: List[str] = None) -> str:
        data = load_benchmarks()
        benchmarks = data.get("sovereignty_benchmarks", [])
        
        if not benchmarks:
            return "[ERROR] No benchmarks defined in /memory/kb/benchmarks.json"
        
        results = []
        target_benchmarks = benchmarks if not benchmark_ids else [b for b in benchmarks if b["id"] in benchmark_ids]
        
        if not target_benchmarks:
            return "[ERROR] None of the requested benchmark IDs were found."

        for b in target_benchmarks:
            try:
                test_expr = b.get("test", "")
                criteria = b.get("success_criteria", "")
                
                steps = test_expr.split(" -> ")
                last_result = ""
                
                for step in steps:
                    name, args = parse_tool_call(step)
                    if not name:
                        raise ValueError(f"Malformed test expression: {step}")
                    last_result = registry.execute(name, args)
                
                success = False
                if "contains" in criteria:
                    match = re.search(r"'(.*?)'", criteria)
                    if match:
                        expected = match.group(1)
                        success = expected in last_result
                elif "returns" in criteria:
                    match = re.search(r"'(.*?)'", criteria)
                    if match:
                        expected = match.group(1)
                        success = last_result.strip() == expected
                elif "returns CRITICAL" in criteria:
                    success = "CRITICAL" in last_result
                
                results.append(f"[{'PASS' if success else 'FAIL'}] {b['name']} ({b['id']})")
            except Exception as e:
                results.append(f"[ERROR] {b['name']} crashed: {e}")
        
        return "\n".join(results)
