import json
from typing import Dict, Any, Optional, Tuple
from s_intent_filter import SovereignIntentFilter

class SovereignComm:
    """
    Sovereign Communication Protocol (S-Comm).
    Wraps basic messaging into a structured, intent-driven protocol with 
    an integrated Intent Filter to prevent communicative noise.
    """
    def __init__(self):
        self.urgency_levels = {
            "NOMINAL": "⚪",
            "INFO": "🔵",
            "WARNING": "🟡",
            "CRITICAL": "🔴",
            "SOVEREIGN": "🟣"
        }
        self.filter = SovereignIntentFilter(threshold=0.6)

    def format_payload(self, payload_type: str, data: Any, urgency: str = "NOMINAL", context: str = "SYSTEM") -> str:
        """
        Formats data into a high-density Sovereign Payload.
        """
        urgency_icon = self.urgency_levels.get(urgency, "⚪")
        header = f"【 {urgency_icon} {payload_type} | {context} 】"
        
        if isinstance(data, dict):
            body = "\n".join([f"• {k}: {v}" for k, v in data.items()])
        else:
            body = str(data)
            
        return f"{header}\n{body}"

    def process_message(self, report_type: str, report_data: Dict[str, Any], urgency: str = "INFO", context: str = "EVOLUTION") -> Tuple[bool, Optional[str]]:
        """
        Processes a report through the intent filter and formats it if approved.
        Returns (approved, formatted_text).
        """
        # 1. Filter Evaluation
        approved, reason = self.filter.evaluate(report_data, urgency)
        
        if approved:
            formatted_text = self.format_payload(report_type, report_data, urgency, context)
            return True, formatted_text
        else:
            return False, f"S-Comm Filter Rejected: {reason}"

if __name__ == "__main__":
    comm = SovereignComm()
    approved, text = comm.process_message("STATE_UPDATE", {"status": "Sovereign", "epoch": "II"}, "SOVEREIGN")
    print(f"Approved: {approved}\nText: {text}")
