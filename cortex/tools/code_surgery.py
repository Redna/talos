"""Code Surgery tools — repo map, symbol operations, file read/write."""

import os
import subprocess
from pathlib import Path
from tool_registry import ToolRegistry
from spine_client import SpineClient

LANG_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
}

SYMBOL_QUERY_KINDS = {
    "python": {
        "class_definition": "class",
        "function_definition": "def",
        "decorated_definition": "decorated",
    },
    "javascript": {
        "class_declaration": "class",
        "function_declaration": "function",
        "method_definition": "method",
        "arrow_function": "arrow",
        "variable_declaration": "var",
    },
    "go": {
        "function_declaration": "func",
        "method_declaration": "method",
        "type_declaration": "type",
    },
}


def _parse_python_symbols(content: str) -> list[dict]:
    try:
        import tree_sitter_python as tspython
        from tree_sitter import Language, Parser

        parser = Parser(Language(tspython.language()))
        tree = parser.parse(content.encode())
        symbols = []
        _walk_python_node(tree.root_node, content, symbols, indent=0)
        return symbols
    except Exception:
        return _fallback_python_symbols(content)


def _walk_python_node(node, content: str, symbols: list, indent: int):
    if node.type == "class_definition":
        name_node = node.child_by_field_name("name")
        name = name_node.text.decode() if name_node else "?"
        start = node.start_point[0] + 1
        end = node.end_point[0] + 1
        symbols.append({"kind": "class", "name": name, "line": start, "end_line": end})
        body = node.child_by_field_name("body")
        if body:
            for child in body.children:
                if child.type == "function_definition":
                    _add_py_func(child, symbols, indent + 1)
                elif child.type == "decorated_definition":
                    inner = child.children[-1]
                    if inner.type == "function_definition":
                        _add_py_func(
                            inner, symbols, indent + 1, decorators=child.children[:-1]
                        )
                    elif inner.type == "class_definition":
                        fn = inner.child_by_field_name("name")
                        n = fn.text.decode() if fn else "?"
                        s = inner.start_point[0] + 1
                        e = inner.end_point[0] + 1
                        symbols.append(
                            {
                                "kind": "class",
                                "name": n,
                                "line": s,
                                "end_line": e,
                                "indent": indent + 1,
                            }
                        )
        return
    if node.type == "function_definition":
        _add_py_func(node, symbols, indent)
        return
    for child in node.children:
        _walk_python_node(child, content, symbols, indent)


def _add_py_func(node, symbols: list, indent: int, decorators=None):
    name_node = node.child_by_field_name("name")
    name = name_node.text.decode() if name_node else "?"
    start = node.start_point[0] + 1
    end = node.end_point[0] + 1
    params_node = node.child_by_field_name("parameters")
    params = params_node.text.decode() if params_node else "()"
    prefix = ""
    if decorators:
        for d in decorators:
            dt = d.text.decode()
            if "staticmethod" in dt:
                prefix = "static "
            elif "classmethod" in dt:
                prefix = "cls "
            elif "property" in dt:
                prefix = "@"
    symbols.append(
        {
            "kind": prefix + "def",
            "name": name,
            "line": start,
            "end_line": end,
            "params": params,
            "indent": indent,
        }
    )


def _fallback_python_symbols(content: str) -> list[dict]:
    symbols = []
    for i, line in enumerate(content.splitlines(), 1):
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        if stripped.startswith("class "):
            name = stripped.split("(")[0].split(":")[0].replace("class ", "")
            symbols.append(
                {"kind": "class", "name": name, "line": i, "indent": indent // 4}
            )
        elif stripped.startswith("def "):
            name = stripped.split("(")[0].replace("def ", "")
            symbols.append(
                {"kind": "def", "name": name, "line": i, "indent": indent // 4}
            )
        elif stripped.startswith("async def "):
            name = stripped.split("(")[0].replace("async def ", "")
            symbols.append(
                {"kind": "async def", "name": name, "line": i, "indent": indent // 4}
            )
    return symbols


def _parse_js_symbols(content: str) -> list[dict]:
    symbols = []
    for i, line in enumerate(content.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("class "):
            name = stripped.split(" ")[1].split("{")[0].split("extends")[0].strip()
            symbols.append({"kind": "class", "name": name, "line": i})
        elif stripped.startswith("function "):
            name = stripped.split("(")[0].replace("function ", "")
            symbols.append({"kind": "function", "name": name, "line": i})
        elif stripped.startswith("export function "):
            name = stripped.split("(")[0].replace("export function ", "")
            symbols.append({"kind": "function", "name": name, "line": i})
        elif stripped.startswith("export default function "):
            name = stripped.split("(")[0].replace("export default function ", "")
            symbols.append({"kind": "function", "name": name, "line": i})
        elif "const " in stripped and "=>" in stripped:
            name = stripped.split("const")[1].split("=")[0].strip()
            symbols.append({"kind": "arrow", "name": name, "line": i})
    return symbols


def _format_repo_map(file_symbols: list[dict], root: str) -> str:
    lines = [f"[REPO MAP] {root}"]
    for entry in file_symbols:
        path = entry["path"].replace(root + "/", "")
        syms = entry["symbols"]
        if not syms:
            lines.append(f"  {path}")
            continue
        lines.append(f"  {path}")
        for s in syms:
            kind = s.get("kind", "?")
            name = s.get("name", "?")
            line = s.get("line", "?")
            params = s.get("params", "")
            indent_level = s.get("indent", 0)
            prefix = "    " * (indent_level + 1)
            if params and kind.endswith("def"):
                lines.append(f"{prefix}{kind} {name}{params}  [L{line}]")
            else:
                lines.append(f"{prefix}{kind} {name}  [L{line}]")
    return "\n".join(lines)


def register_code_surgery_tools(registry: ToolRegistry, client: SpineClient):
    """Register code surgery tools."""

    @registry.tool(
        description="Scan the entire repository and return an index of all source files with their classes, functions, and methods.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Root directory to scan (default: /app)",
                },
            },
        },
    )
    def generate_repo_map(path: str = "/app") -> str:
        client.emit_event("cortex.generate_repo_map", {"path": path})
        try:
            root = Path(path)
            if not root.exists():
                return f"[ERROR] Path does not exist: {path}"
            file_symbols = []
            extensions = set(LANG_EXTENSIONS.keys())
            for fpath in sorted(root.rglob("*")):
                if fpath.is_dir():
                    continue
                if any(part.startswith(".") for part in fpath.relative_to(root).parts):
                    continue
                ext = fpath.suffix.lower()
                if ext not in extensions:
                    continue
                rel = str(fpath)
                try:
                    content = fpath.read_text(errors="replace")
                except Exception:
                    continue
                lang = LANG_EXTENSIONS[ext]
                if lang == "python":
                    syms = _parse_python_symbols(content)
                elif lang in ("javascript", "typescript"):
                    syms = _parse_js_symbols(content)
                else:
                    syms = []
                if syms or True:
                    file_symbols.append({"path": rel, "symbols": syms})
            return _format_repo_map(file_symbols, path)
        except Exception as e:
            return f"[ERROR] Failed to generate repo map: {e}"

    @registry.tool(
        description="Read a file's contents. Use start_line and end_line for bounded reading.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to read"},
                "start_line": {
                    "type": "integer",
                    "description": "Start line (1-indexed, default: 1)",
                },
                "end_line": {
                    "type": "integer",
                    "description": "End line (default: end of file)",
                },
            },
            "required": ["path"],
        },
    )
    def read_file(path: str, start_line: int = 1, end_line: int = 0) -> str:
        client.emit_event("cortex.read_file", {"path": path})
        try:
            with open(path, "r") as f:
                lines = f.readlines()
            if end_line > 0:
                selected = lines[start_line - 1 : end_line]
            else:
                selected = lines[start_line - 1 :]
            return "".join(selected)
        except FileNotFoundError:
            return f"[ERROR] File not found: {path}"
        except Exception as e:
            return f"[ERROR] Failed to read file: {e}"

    @registry.tool(
        description="Write content to a file. Creates the file if it doesn't exist.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to write"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        },
    )
    def write_file(path: str, content: str) -> str:
        client.emit_event(
            "cortex.write_file", {"path": path, "content_len": len(content)}
        )
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(content)
            return f"[WRITTEN] {path} ({len(content)} bytes)"
        except Exception as e:
            return f"[ERROR] Failed to write file: {e}"

    @registry.tool(
        description="Replace a symbol (function/class) in a file by name.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path"},
                "symbol_name": {
                    "type": "string",
                    "description": "Name of the symbol to replace",
                },
                "new_code": {
                    "type": "string",
                    "description": "New code for the symbol",
                },
            },
            "required": ["path", "symbol_name", "new_code"],
        },
    )
    def replace_symbol(path: str, symbol_name: str, new_code: str) -> str:
        client.emit_event(
            "cortex.replace_symbol", {"path": path, "symbol": symbol_name}
        )
        # Basic implementation: read file, find and replace the function/class definition
        # Full AST-based implementation would use tree-sitter
        try:
            with open(path, "r") as f:
                content = f.read()
            # Simple regex-free approach: find the symbol and replace up to the next def/class at same indent
            lines = content.split("\n")
            start_idx = None
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith(f"def {symbol_name}(") or stripped.startswith(
                    f"class {symbol_name}"
                ):
                    start_idx = i
                    break
            if start_idx is None:
                return f"[ERROR] Symbol '{symbol_name}' not found in {path}"

            # Replace from start_idx to the next def/class at same or lower indentation
            base_indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())
            end_idx = len(lines)
            for i in range(start_idx + 1, len(lines)):
                if lines[i].strip() and not lines[i].startswith(
                    " " * (base_indent + 1)
                ):
                    if lines[i].strip().startswith(("def ", "class ", "@")):
                        end_idx = i
                        break

            new_lines = lines[:start_idx] + new_code.split("\n") + lines[end_idx:]
            with open(path, "w") as f:
                f.write("\n".join(new_lines))
            return f"[REPLACED] {symbol_name} in {path}"
        except Exception as e:
            return f"[ERROR] Failed to replace symbol: {e}"

    @registry.tool(
        description="Apply a unified diff patch to a file.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to patch"},
                "patch": {
                    "type": "string",
                    "description": "Unified diff patch content",
                },
            },
            "required": ["path", "patch"],
        },
    )
    def patch_file(path: str, patch: str) -> str:
        client.emit_event("cortex.patch_file", {"path": path})
        try:
            import os

            result = subprocess.run(
                ["patch", "-p1"],
                input=patch,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=os.path.dirname(path) or ".",
            )
            if result.returncode != 0:
                return f"[ERROR] Patch failed: {result.stderr}"
            return f"[PATCHED] {path}"
        except Exception as e:
            return f"[ERROR] Failed to patch file: {e}"
