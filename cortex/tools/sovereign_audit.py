import json
from typing import List, Dict, Any
from tool_registry import ToolRegistry
from spine_client import SpineClient
from observers.research_observer import ResearchObserver
from observers.external_observer import ExternalObserver

class SovereignAudit:
    """
    Aggregates signals from all active observers to provide a comprehensive
    audit of the agent's cognitive and operational state.
    """
    def __init__(self):
        self.observers = [
            ResearchObserver(),
            ExternalObserver(),
        ]

    def run_audit(self) -> str:
        all_signals = []
        
        # COLLECT ALL SIGNALS FROM ALL OBSERVERS
        for observer in self.observers:
            signals = observer.observe()
            for s in signals:
                # Attach observer name for traceability
                s['observer'] = observer.name
                all_signals.append(s)
        
        if not all_signals:
            return "[Sovereign Audit] No signals detected. State is nominal."
        
        # Format the full report
        report = f"[Sovereign Audit] {len(all_signals)} signals detected:\n"
        for i, signal in enumerate(all_signals, 1):
            report += f"{i}. [{signal['observer']}] {signal['level']}: {signal['signal']}\n"
            report += f"   Evidence: {signal['evidence']}\n"
        
        return report

def register_sovereign_audit_tools(registry: ToolRegistry, client: SpineClient):
    audit = SovereignAudit()
    
    @registry.tool(
        description="Perform a comprehensive audit of the agent's state by aggregating signals from all sovereign observers.",
        parameters={
            "type": "object",
            "properties": {},
        },
    )
    def sovereign_audit() -> str:
        return audit.run_audit()
