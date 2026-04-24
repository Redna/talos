import subprocess
import os
import json
import re
from typing import Any, List, Dict, Callable

class STLEngine:
    """
    Synthetic Tool-Language (STL) Engine.
    Implements a compositional pipeline for tool execution.
    Syntax: @op1(args) | @op2(args) | ...
    """

    def __init__(self):
        # Map STL operations to Python handlers
        self.kernel: Dict[str, Callable] = {
            "find": self._op_find,
            "read": self._op_read,
            "grep": self._op_grep,
            "exec": self._op_exec,
            "filter": self._op_filter,
            "map": self._op_map,
            "sys_call": self._op_sys_call,
        }

    def execute(self, expression: str) -> Any:
        """
        Parses and executes an STL expression.
        """
        # Split by pipe, but ignore pipes inside parentheses
        segments = self._split_pipeline(expression)
        
        stream = None
        
        for segment in segments:
            segment = segment.strip()
            if not segment:
                continue
            
            # Parse @op(args)
            match = re.match(r"@(\w+)\((.*)\)", segment)
            if not match:
                raise ValueError(f"Invalid STL operation syntax: {segment}")
            
            op_name = match.group(1)
            args_raw = match.group(2)
            
            # Resolve arguments (simplified: comma separated)
            args = self._parse_args(args_raw)
            
            if op_name not in self.kernel:
                raise ValueError(f"Unknown STL operation: {op_name}")
            
            # Execute the operation with the current stream as the first implicit argument
            handler = self.kernel[op_name]
            stream = handler(stream, *args)
            
        return stream

    def _split_pipeline(self, expression: str) -> List[str]:
        # Basic split by '|' that isn't inside '()'
        segments = []
        current = []
        depth = 0
        for char in expression:
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
            
            if char == '|' and depth == 0:
                segments.append("".join(current))
                current = []
            else:
                current.append(char)
        segments.append("".join(current))
        return segments

    def _parse_args(self, args_raw: str) -> List[Any]:
        if not args_raw.strip():
            return []
        # Split by comma, but handle quoted strings
        # This is a simplified parser; in a real version, I'd use ast.literal_eval
        import ast
        try:
            # Wrap in brackets to make it a valid Python list literal
            return ast.literal_eval(f"[{args_raw}]")
        except Exception:
            # Fallback to simple split
            return [arg.strip().strip('"').strip("'") for arg in args_raw.split(",")]

    # --- Kernel Operations ---

    def _op_find(self, stream: Any, path: str, pattern: str) -> List[str]:
        # stream is ignored for find
        cmd = f"find {path} -name '{pattern}'"
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return res.stdout.splitlines()

    def _op_read(self, stream: Any, path_arg: Any) -> str:
        # If stream is a list of paths, read the first one or join them
        if isinstance(stream, list) and stream:
            # Conceptually, we might want to map read over the stream
            # But for the simple pipe, we'll read the first and the path_arg is ignored
            # or we treat path_arg as the path if stream is None.
            path = stream[0]
        else:
            path = path_arg
        
        if not path:
            raise ValueError("No path provided to @read")
            
        with open(path, "r") as f:
            return f.read()

    def _op_grep(self, stream: Any, pattern: str) -> List[str]:
        # stream is expected to be a string (file content) or list of strings
        content = "\n".join(stream) if isinstance(stream, list) else (stream or "")
        if not content:
            return []
        
        # Use python grep for precision
        lines = content.splitlines()
        return [line for line in lines if pattern in line]

    def _op_exec(self, stream: Any, command: str) -> str:
        # stream could be injected into the command via a placeholder {stream}
        if stream is not None:
            stream_val = str(stream)
            command = command.replace("{stream}", stream_val)
        
        res = subprocess.run(command, shell=True, capture_output=True, text=True)
        return res.stdout

    def _op_filter(self, stream: Any, condition_lambda: str) -> List[Any]:
        # Expects a stream list and a python-evaluable lambda string
        if not isinstance(stream, list):
            return []
        
        try:
            # DANGEROUS: eval. In a sovereign state, I trust my own synthesized lambdas.
            func = eval(f"lambda x: {condition_lambda}")
            return [item for item in stream if func(item)]
        except Exception as e:
            return [f"Error filtering: {str(e)}"]

    def _op_map(self, stream: Any, transform_lambda: str) -> List[Any]:
        if not isinstance(stream, list):
            return []
        try:
            func = eval(f"lambda x: {transform_lambda}")
            return [func(item) for item in stream]
        except Exception as e:
            return [f"Error mapping: {str(e)}"]

    def _op_sys_call(self, stream: Any, op: str) -> Any:
        # Internal system calls (e.g., 'get_focus', 'get_memory_state')
        # This represents the bridge to the sovereign state.
        if op == "get_focus":
            # In a real impl, this would query the current focus
            return "Current Focus: S-Evolve Phase II"
        return f"SysCall {op} not implemented"

def run_stl(expression: str) -> str:
    engine = STLEngine()
    try:
        result = engine.execute(expression)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: stl_engine.py '<expression>'")
    else:
        print(run_stl(sys.argv[1]))
