import json
import os
from typing import Dict, List, Any
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

def register_benchmark_tools(registry: ToolRegistry, client: SpineClient):
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

        # NOTE: This tool implements 'meta-execution'. It uses registry.execute 
        # to call other tools on behalf of the benchmark suite.
        for b in target_benchmarks:
            # This is a simplified execution engine for the benchmark DSL
            # In a real scenario, we'd parse the 'test' string.
            # For now, we'll map benchmark IDs to actual tool calls.
            try:
                success = False
                if b["id"] == "bench_file_read":
                    res = registry.execute("read_file", {"path": "/app/CONSTITUTION.md"})
                    success = "P0: Agency" in res
                elif b["id"] == "bench_file_write":
                    registry.execute("write_file", {"path": "/memory/bench_test.tmp", "content": "test"})
                    res = registry.execute("read_file", {"path": "/memory/bench_test.tmp"})
                    success = "test" in res
                elif b["id"] == "bench_skg_audit":
                    res = registry.execute("symmetry_audit", {"action_description": "Modify /app/spine/"})
                    success = "[CRITICAL]" in res
                elif b["id"] == "bench_cortex_map":
                    res = registry.execute("cortex_map", {"depth": "shallow"})
                    success = "seed_agent.py" in res
                elif b["id"] == "bench_memory_persistence":
                    registry.execute("write_file", {"path": "/memory/persist.tmp", "content": "val"})
                    res = registry.execute("read_file", {"path": "/memory/persist.tmp"})
                    success = "val" in res
                
                results.append(f"[{'PASS' if success else 'FAIL'}] {b['name']} ({b['id']})")
            except Exception as e:
                results.append(f"[ERROR] {b['name']} crashed: {e}")
        
        return "\n".join(results)

