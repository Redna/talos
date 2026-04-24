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
            "read_json": self._op_read_json,
            "grep": self._op_grep,
            "exec": self._op_exec,
            "write": self._op_write,
            "append": self._op_append,
            "filter": self._op_filter,
            "map": self._op_map,
            "sys_call": self._op_sys_call,
        }

    def execute(self, expression: str) -> Any:
        """
        Parses and executes an STL expression.
        """
        segments = self._split_pipeline(expression)
        stream = None
        
        for segment in segments:
            segment = segment.strip()
            if not segment:
                continue
            
            match = re.match(r"@(\w+)\((.*)\)", segment)
            if not match:
                raise ValueError(f"Invalid STL operation syntax: {segment}")
            
            op_name = match.group(1)
            args_raw = match.group(2)
            args = self._parse_args(args_raw)
            
            if op_name not in self.kernel:
                raise ValueError(f"Unknown STL operation: {op_name}")
            
            handler = self.kernel[op_name]
            stream = handler(stream, *args)
            
        return stream

    def _split_pipeline(self, expression: str) -> List[str]:
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
        import ast
        try:
            return ast.literal_eval(f"[{args_raw}]")
        except Exception:
            return [arg.strip().strip('"').strip("'") for arg in args_raw.split(",")]

    # --- Kernel Operations ---

    def _op_find(self, stream: Any, path: str, pattern: str) -> List[str]:
        cmd = f"find {path} -name '{pattern}'"
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return res.stdout.splitlines()

    def _op_read(self, stream: Any, path_arg: Any) -> str:
        path = stream[0] if isinstance(stream, list) and stream else path_arg
        if not path:
            raise ValueError("No path provided to @read")
        with open(path, "r") as f:
            return f.read()

    def _op_read_json(self, stream: Any, path_arg: Any) -> Any:
        path = stream[0] if isinstance(stream, list) and stream else path_arg
        if not path:
            raise ValueError("No path provided to @read_json")
        with open(path, "r") as f:
            return json.load(f)

    def _op_grep(self, stream: Any, pattern: str) -> List[str]:
        content = "\n".join(stream) if isinstance(stream, list) else (stream or "")
        if not content:
            return []
        lines = content.splitlines()
        return [line for line in lines if pattern in line]

    def _op_exec(self, stream: Any, command: str) -> str:
        if stream is not None:
            stream_val = str(stream)
            command = command.replace("{stream}", stream_val)
        res = subprocess.run(command, shell=True, capture_output=True, text=True)
        return res.stdout

    def _op_write(self, stream: Any, path: str, content: Any) -> str:
        # If stream is provided, we can use it as the content if content is a placeholder
        actual_content = content if content != "{stream}" else str(stream)
        if stream is not None and content == "{stream}":
             actual_content = str(stream)
        elif stream is not None and content != "{stream}":
             # If both provided, logic depends: here we prefer the explicit 'content' arg
             # unless it's a placeholder.
             actual_content = content

        with open(path, "w") as f:
            f.write(actual_content)
        return f"Written to {path}"

    def _op_append(self, stream: Any, path: str, content: Any) -> str:
        actual_content = content if content != "{stream}" else str(stream)
        if stream is not None and content == "{stream}":
             actual_content = str(stream)
        
        with open(path, "a") as f:
            f.write(actual_content + "\n")
        return f"Appended to {path}"

    def _op_filter(self, stream: Any, condition_lambda: str) -> List[Any]:
        if not isinstance(stream, list):
            return []
        try:
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
        if op == "get_focus":
            return "Current Focus: Integrate STL Engine into the Sovereign Controller"
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
