import os
from typing import List, Dict, NamedTuple
from tree_sitter import Language, Parser
import tree_sitter_python

class Symbol(NamedTuple):
    name: str
    kind: str  # 'class' or 'function'
    start_line: int
    end_line: int
    start_col: int
    end_col: int

class RepoMapper:
    def __init__(self, root_path: str):
        self.root_path = root_path
        self.language = Language(tree_sitter_python.language())
        self.parser = Parser(self.language)

    def scan(self) -> Dict[str, List[Symbol]]:
        repo_map = {}
        for root, _, files in os.walk(self.root_path):
            for file in files:
                if file.endswith(".py"):
                    path = os.path.join(root, file)
                    rel_path = os.path.relpath(path, self.root_path)
                    symbols = self._extract_symbols(path)
                    if symbols:
                        repo_map[rel_path] = symbols
        return repo_map

    def _extract_symbols(self, path: str) -> List[Symbol]:
        with open(path, "rb") as f:
            content = f.read()
        
        tree = self.parser.parse(content)
        root_node = tree.root_node
        symbols = []

        # Define queries for classes and functions
        query_scm = """
        (class_definition
            name: (identifier) @class_name) @class_def
        (function_definition
            name: (identifier) @func_name) @func_def
        """
        query = self.language.query(query_scm)
        captures = query.captures(root_node)

        # tree-sitter query returns a list of (node, capture_name)
        # We need to group them by the definition node
        defs = {}
        for node, name in captures:
            if name == "class_def" or name == "func_def":
                defs[node] = {"kind": "class" if name == "class_def" else "function", "node": node}
            elif name == "class_name" or name == "func_name":
                # The name node is a child of the def node; find which one it belongs to
                parent = node.parent
                if parent in defs:
                    defs[parent]["name_node"] = node

        for def_node, info in defs.items():
            name_node = info.get("name_node")
            if name_node:
                name = content[name_node.start_byte:name_node.end_byte].decode("utf8")
                symbols.append(Symbol(
                    name=name,
                    kind=info["kind"],
                    start_line=def_node.start_point[0] + 1,
                    end_line=def_node.end_point[0] + 1,
                    start_col=def_node.start_point[1],
                    end_col=def_node.end_point[1]
                ))
        
        return symbols
