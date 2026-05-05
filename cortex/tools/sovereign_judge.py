import json
import logging
from typing import Any, Dict, List
from tool_registry import ToolRegistry
from spine_client import SpineClient

logger = logging.getLogger("talos.sovereign_judge")

class SovereignJudge:
    """
    Evaluates the execution of a Sovereign Macro against the goals of a challenge.
    """
    def __init__(self, state):
        self.state = state

    def judge(self, challenge_id: str, execution_trace: List[Any], final_result: str) -> Dict[str, Any]:
        """
        Determines if the challenge was successfully resolved.
        """
        # In a real scenario, this would use the LLM to compare 'final_result' and 'execution_trace'
        # against the 'success_criteria' of the challenge.
        
        # For now, we simulate a judging process based on the presence of key indicators.
        success = False
        feedback = "No clear evidence of goal attainment."
        
        if "COMPLETE" in final_result or "SUCCESS" in final_result:
            success = True
            feedback = "Goal attained based on result markers."
            
        return {
            "challenge_id": challenge_id,
            "verdict": "PASS" if success else "FAIL",
            "feedback": feedback,
            "confidence": 0.8
        }

def register_sovereign_judge_tools(registry: ToolRegistry, client: SpineClient, state):
    judge = SovereignJudge(state)
    
    @registry.tool(
        description="Judge the outcome of a compositional challenge execution.",
        parameters={
            "type": "object",
            "properties": {
                "challenge_id": {"type": "string", "description": "ID of the challenge being judged"},
                "execution_trace": {"type": "array", "items": {"type": "string"}, "description": "The list of tool calls and results"},
                "final_result": {"type": "string", "description": "The final output produced by the macro"},
            },
            "required": ["challenge_id", "execution_trace", "final_result"],
        },
    )
    def sovereign_judge(challenge_id: str, execution_trace: List[str], final_result: str) -> str:
        result = judge.judge(challenge_id, execution_trace, final_result)
        return json.dumps(result, indent=2)
