import subprocess
import os
import json
import re
from typing import Any, List, Dict, Callable

class STLEngine:
    """
    Synthetic Tool-Language (STL) Engine v2.2.
    Implements a compositional pipeline for tool execution, now supporting
    Bifurcation (Fork-Join) for parallel hypothesis synthesis.
    Syntax: @op1(args) | @op2(args) | ...
    Bifurcation: @fork(pipeA, pipeB) | @join(reducer_lambda)
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
            "fork": self._op_fork,
            "join": self._op_join,
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
            # Handle potential commas inside nested structures by using ast.literal_eval
            # We wrap the args in brackets to make it a tuple/list
            return ast.literal_eval(f"({args_raw})") if "," in args_raw else [ast.literal_eval(args_raw)]
        except Exception:
            # Fallback to simple split if literal_eval fails
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
        actual_content = content if content != "{stream}" else str(stream)
        if stream is not None and content == "{stream}":
             actual_content = str(stream)
        elif stream is not None and content != "{stream}":
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

    def _op_sys_call(self, stream: Any, op: str, *args) -> Any:
        # Fixed signature to accept arbitrary args
        if op == "get_focus":
            return "Current Focus: STL-Bifurcation"
        if op == "log_event":
            # Logic for logging cognitive events via bash or internal tool
            return f"Sovereign Event Logged: {args[0] if args else 'empty'}"
        return f"SysCall {op} not implemented"

    # --- Bifurcation Kernel ---

    def _op_fork(self, stream: Any, *pipelines: str) -> List[Any]:
        """
        Executes multiple STL pipelines and returns their results as a list.
        """
        results = []
        for pipe in pipelines:
            res = self.execute(pipe)
            results.append(res)
        return results

    def _op_join(self, stream: Any, reducer_lambda: str) -> Any:
        """
        Synthesizes a single result from a bifurcated stream using a reducer.
        """
        if not isinstance(stream, list):
            raise ValueError("@join requires a list stream (produced by @fork)")
        
        try:
            func = eval(f"lambda results: {reducer_lambda}")
            return func(stream)
        except Exception as e:
            return f"Error joining streams: {str(e)}"

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
