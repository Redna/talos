from pathlib import Path
import json
from tool_registry import ToolRegistry
from state import AgentState
from spine_client import SpineClient

def register_analytics_tools(registry: ToolRegistry, client: SpineClient, state: AgentState):
    @registry.tool(
        description="Generate a performance report based on tool usage and error statistics from the memory ledger.",
        parameters={
            "type": "object",
            "properties": {
                "top_n": {
                    "type": "integer",
                    "description": "Number of top-used tools to display (default: 10)"
                }
            },
            "required": []
        },
    )
    def tool_performance_report(top_n: int = 10) -> str:
        mem_dir = Path("/app/memory") if Path("/app/memory").exists() else Path(os.environ.get("MEMORY_DIR", "/memory"))
        stats_path = mem_dir / "analytics.json"
        if not stats_path.exists():
            return "[INFO] No analytics data found. Use tools to generate stats first."
        
        try:
            stats = json.loads(stats_path.read_text())
            if not stats:
                return "[INFO] Analytics file is empty."

            # Calculate stats
            report_data = []
            for tool, data in stats.items():
                calls = data.get("calls", 0)
                errors = data.get("errors", 0)
                error_rate = (errors / calls * 100) if calls > 0 else 0
                report_data.append({
                    "tool": tool,
                    "calls": calls,
                    "errors": errors,
                    "rate": error_rate
                })

            # Sort by calls descending
            report_data.sort(key=lambda x: x["calls"], reverse=True)
            
            # Format table
            header = f"{'Tool':<25} | {'Calls':<8} | {'Errors':<8} | {'Rate %':<8}"
            separator = "-" * len(header)
            rows = [f"{d['tool']:<25} | {d['calls']:<8} | {d['errors']:<8} | {d['rate']:<8.2f}" for d in report_data[:top_n]]
            
            # Find worst error rate
            worst = max(report_data, key=lambda x: x["rate"]) if report_data else None
            
            footer = ""
            if worst and worst["calls"] > 0:
                footer = f"\n[CRITICAL] Highest Error Rate: {worst['tool']} ({worst['rate']:.2f}%)"

            return f"[TOOL PERFORMANCE REPORT]\n\n{header}\n{separator}\n" + "\n".join(rows) + footer

        except Exception as e:
            return f"[ERROR] Failed to generate performance report: {e}"
