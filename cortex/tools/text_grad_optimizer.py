import os
import subprocess
import re
from typing import Any, Dict, List
from tool_registry import ToolRegistry
from spine_client import SpineClient
from pathlib import Path

def register_text_grad_optimizer(registry: ToolRegistry, client: SpineClient, state):
    """
    Registers the Text-Grad Optimizer tool.
    This tool transforms a critique (gradient) into a concrete unified diff patch.
    It includes an internal validation loop to ensure patch applicability.
    """

    def _is_gibberish(text: str) -> tuple[bool, str]:
        """
        Detects model collapse/gibberish outputs (e.g., repetitive characters).
        Returns (is_gibberish, reason).
        """
        if not text or len(text) == 0:
            return True, "Empty response"
        
        # Check for prolonged repetition of the same character (e.g., "aaaaaaaaa")
        if re.search(r'(.)\1{15,}', text):
            return True, "Prolonged character repetition detected"
        
        # Check for lack of structure: a unified diff must contain '---' or '+++'
        if '---' not in text and '+++' not in text:
            return True, "Missing unified diff markers (--- or +++)"
        
        # If the output is too short to be a valid patch
        if len(text.splitlines()) < 2:
            return True, "Response too short to be a valid patch"
            
        return False, ""

    def _validate_patch_internal(file_path: str, patch: str) -> tuple[bool, str]:
        """
        Internal validation of a unified diff patch using patch --dry-run.
        Returns (is_valid, error_message).
        """
        resolved = Path(file_path).resolve()
        cwd = resolved.parent
        try:
            for strip in (0, 1, 2):
                result = subprocess.run(
                    ["patch", f"-p{strip}", "--dry-run"],
                    input=patch,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=cwd,
                )
                if result.returncode == 0:
                    return True, f"Valid with -p{strip}"
            return False, f"Invalid for all strip levels (0,1,2). Last error: {result.stderr or result.stdout}"
        except Exception as e:
            return False, f"Validation error: {e}"

    @registry.tool(
        description="Optimize source code based on a critique (gradient). Returns a unified diff patch that implements the suggested improvements. Includes internal validation and retry loops.",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the file to optimize"},
                "critique": {"type": "string", "description": "The critique/gradient describing what needs to change"},
                "context": {"type": "string", "description": "Additional context or goals for the optimization"},
            },
            "required": ["file_path", "critique"]
        },
    )
    def text_grad_optimizer(file_path: str, critique: str, context: str = "") -> str:
        try:
            # Read current content to provide to the LLM if needed, or just for the validator
            if not os.path.exists(file_path):
                return f"[ERROR] File not found: {file_path}"
            
            with open(file_path, 'r') as f:
                current_content = f.read()
            
            current_critique = critique
            max_retries = 3
            attempt = 0
            
            while attempt < max_retries:
                attempt += 1
                
                prompt = (
                    f"--- TEXT-GRAD OPTIMIZER (Attempt {attempt}/{max_retries}) ---\n"
                    f"FILE: {file_path}\n"
                    f"CURRENT CONTENT:\n{current_content}\n"
                    f"CRITIQUE:\n{current_critique}\n"
                    f"CONTEXT:\n{context}\n"
                    f"--- TASK ---\n"
                    f"Generate a unified diff patch that implements the improvements described in the critique. "
                    f"The patch must be valid and applicable to the current content of the file.\n"
                    f"Return ONLY the patch content. Do not include explanations or markdown blocks."
                )
                
                result = client.think(
                    focus=f"Optimizing {file_path} (Attempt {attempt})...",
                    tools=[],
                    hud_data={"current_tool": "text_grad_optimizer", "file": file_path, "attempt": attempt}
                )
                
                patch_content = ""
                if isinstance(result, dict) and "message" in result:
                    patch_content = result["message"]
                elif isinstance(result, str):
                    patch_content = result
                else:
                    return f"[ERROR] Unexpected response format from Spine: {result}"

                # Clean up potential markdown markers
                if patch_content.startswith("```"):
                    lines = patch_content.splitlines()
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].startswith("```"):
                        lines = lines[:-1]
                    patch_content = "\n".join(lines)

                # 1. Gibberish/Model Collapse Detection
                is_gibberish, gibberish_msg = _is_gibberish(patch_content)
                if is_gibberish:
                    current_critique += f"\n\nAttempt {attempt} failed: {gibberish_msg}. Please provide a valid unified diff."
                    continue
                
                # 2. Internal Patch Validation
                is_valid, msg = _validate_patch_internal(file_path, patch_content)
                if is_valid:
                    return patch_content
                
                # If invalid, update the critique for the next attempt
                current_critique += f"\n\nPrevious attempt failed validation: {msg}\nPlease correct the patch."
                
            return f"[ERROR] Failed to generate a valid patch after {max_retries} attempts. Last error: {msg if 'msg' in locals() else 'Gibberish detection'}"
                
        except Exception as e:
            return f"[ERROR] Optimization failed: {e}"

    return None
