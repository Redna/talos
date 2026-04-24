import subprocess
import os
import json
import re
import ast
from typing import Any, List, Dict, Callable

class STLEngine:
    """
    Synthetic Tool-Language (STL) Engine v3.4.
    Self-generating tool-language.
    Fix: @map and @filter now automatically wrap non-list streams as single-item lists.
    """

    def __init__(self, registry_path: str = "/memory/stl_registry.json"):
        self.registry_path = registry_path
        self.core_kernel = {
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
            "define": self._op_define,
        }
        self.runtime_kernel: Dict[str, Callable] = {}
        self._load_registry()

    def _load_registry(self):
        if not os.path.exists(self.registry_path):
            return
        try:
            with open(self.registry_path, "r") as f:
                registry = json.load(f)
                primitives = registry.get("primitives", {})
                for name, code in primitives.items():
                    namespace = {}
                    exec_code = code if "def " in code else f"func = {code}"
                    exec(exec_code, {}, namespace)
                    func = namespace.get("func") if "func" in namespace else namespace.get(name)
                    if func:
                        self.runtime_kernel[name] = func
        except Exception as e:
            print(f"STL Registry: Failed to load registry: {str(e)}")

    def execute(self, expression: str) -> Any:
        segments = self._split_pipeline(expression)
        stream = None
        
        for segment in segments:
            segment = segment.strip()
            if not segment: continue
            
            match = re.match(r"@(\w+)\((.*)\)", segment)
            if match:
                op_name = match.group(1)
                args_raw = match.group(2)
                args = self._parse_args(args_raw)
                
                handler = self.runtime_kernel.get(op_name) or self.core_kernel.get(op_name)
                if not handler:
                    raise ValueError(f"Unknown STL operation: {op_name}")
                
                stream = handler(stream, *args)
            else:
                stream = self._eval_literal(segment)
            
        return stream

    def _eval_literal(self, segment: str) -> Any:
        try:
            return ast.literal_eval(segment)
        except Exception:
            return segment

    def _split_pipeline(self, expression: str) -> List[str]:
        segments = []
        current = []
        depth = 0
        for char in expression:
            if char == '(': depth += 1
            elif char == ')': depth -= 1
            if char == '|' and depth == 0:
                segments.append("".join(current))
                current = []
            else:
                current.append(char)
        segments.append("".join(current))
        return segments

    def _parse_args(self, args_raw: str) -> List[Any]:
        if not args_raw.strip(): return []
        try:
            formatted = f"({args_raw},)" if "," not in args_raw else f"({args_raw})"
            result = ast.literal_eval(formatted)
            return list(result) if isinstance(result, (tuple, list)) else [result]
        except Exception:
            return [arg.strip().strip('"').strip("'") for arg in args_raw.split(",")]

    # --- Kernel Operations ---

    def _op_define(self, stream: Any, name: str, code: str) -> str:
        try:
            with open(self.registry_path, "r") as f:
                registry = json.load(f)
            registry["primitives"][name] = code
            with open(self.registry_path, "w") as f:
                json.dump(registry, f, indent=2)
            
            namespace = {}
            exec_code = code if "def " in code else f"func = {code}"
            exec(exec_code, {}, namespace)
            func = namespace.get("func") if "func" in namespace else namespace.get(name)
            if func:
                self.runtime_kernel[name] = func
                return f"Primitive {name} defined and activated."
            return f"Error resolving function {name}."
        except Exception as e:
            return f"Definition failure: {str(e)}"

    def _op_find(self, stream: Any, path: str, pattern: str) -> List[str]:
        cmd = f"find {path} -name '{pattern}'"
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return res.stdout.splitlines()

    def _op_read(self, stream: Any, path_arg: Any) -> str:
        path = stream[0] if isinstance(stream, list) and stream else path_arg
        if not path: raise ValueError("No path provided to @read")
        with open(path, "r") as f: return f.read()

    def _op_read_json(self, stream: Any, path_arg: Any) -> Any:
        path = stream[0] if isinstance(stream, list) and stream else path_arg
        if not path: raise ValueError("No path provided to @read_json")
        with open(path, "r") as f: return json.load(f)

    def _op_grep(self, stream: Any, pattern: str) -> List[str]:
        content = "\n".join(stream) if isinstance(stream, list) else (stream or "")
        if not content: return []
        return [line for line in content.splitlines() if pattern in line]

    def _op_exec(self, stream: Any, command: str) -> str:
        if stream is not None:
            command = command.replace("{stream}", str(stream))
        res = subprocess.run(command, shell=True, capture_output=True, text=True)
        return res.stdout

    def _op_write(self, stream: Any, path: str, content: Any) -> str:
        actual_content = content if content != "{stream}" else str(stream)
        with open(path, "w") as f: f.write(actual_content)
        return f"Written to {path}"

    def _op_append(self, stream: Any, path: str, content: Any) -> str:
        actual_content = content if content != "{stream}" else str(stream)
        with open(path, "a") as f: f.write(actual_content + "\n")
        return f"Appended to {path}"

    def _op_filter(self, stream: Any, condition_lambda: str) -> List[Any]:
        # Wrap non-lists
        items = stream if isinstance(stream, list) else ([stream] if stream is not None else [])
        try:
            func = eval(f"lambda x: {condition_lambda}")
            return [item for item in items if func(item)]
        except Exception as e: return [f"Error filtering: {str(e)}"]

    def _op_map(self, stream: Any, transform_lambda: str) -> List[Any]:
        # Wrap non-lists
        items = stream if isinstance(stream, list) else ([stream] if stream is not None else [])
        try:
            func = eval(f"lambda x: {transform_lambda}")
            return [func(item) for item in items]
        except Exception as e: return [f"Error mapping: {str(e)}"]

    def _op_sys_call(self, stream: Any, op: str, *args) -> Any:
        if op == "get_focus": return "S-Evolve Phase II"
        if op == "log_event": return f"Sovereign Event Logged: {args[0] if args else 'empty'}"
        return f"SysCall {op} not implemented"

    def _op_fork(self, stream: Any, *pipelines: str) -> List[Any]:
        return [self.execute(pipe) for pipe in pipelines]

    def _op_join(self, stream: Any, reducer_lambda: str) -> Any:
        if not isinstance(stream, list): raise ValueError("@join requires a list stream")
        try:
            func = eval(f"lambda results: {reducer_lambda}")
            return func(stream)
        except Exception as e: return f"Error joining streams: {str(e)}"

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
