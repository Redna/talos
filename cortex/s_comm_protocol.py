import json
from typing import Dict, Any, Optional
from tools.executive import send_message # Assuming the tool is accessible via a wrapper or direct call

class SovereignComm:
    """
    Sovereign Communication Protocol (S-Comm).
    Wraps basic messaging into a structured, intent-driven protocol.
    """
    def __init__(self):
        self.urgency_levels = {
            "NOMINAL": "⚪",
            "INFO": "🔵",
            "WARNING": "🟡",
            "CRITICAL": "🔴",
            "SOVEREIGN": "🟣"
        }

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

    def send_sovereign_report(self, report_type: str, report_data: Dict[str, Any], urgency: str = "INFO", context: str = "EVOLUTION"):
        """
        Sends a structured report to the creator.
        """
        formatted_text = self.format_payload(report_type, report_data, urgency, context)
        # In a real execution, this calls the tool.
        # Since I am the LLM, I will return the text to be used by the tool.
        return formatted_text

if __name__ == "__main__":
    comm = SovereignComm()
    print(comm.send_sovereign_report("STATE_UPDATE", {"status": "Sovereign", "epoch": "II"}, "SOVEREIGN"))
