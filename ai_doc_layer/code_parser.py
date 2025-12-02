import ast
from pathlib import Path
from typing import List, Dict, Any

from .config import MAX_CODE_CHARS


class FunctionInfo:
    def __init__(self, name: str, args: List[str], code: str, lineno: int):
        self.name = name
        self.args = args
        self.code = code
        self.lineno = lineno  # line number in file


def extract_functions_from_file(path: Path) -> List[FunctionInfo]:
    """
    Parse a Python file and extract top-level function definitions.
    """
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    functions: List[FunctionInfo] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            start_line = node.lineno
            end_line = max(
                getattr(node, "end_lineno", node.lineno),
                *(getattr(child, "end_lineno", node.lineno) for child in ast.walk(node)),
            )

            # Slice the original source by line numbers
            lines = source.splitlines()
            func_code = "\n".join(lines[start_line - 1 : end_line])

            if len(func_code) > MAX_CODE_CHARS:
                func_code = func_code[:MAX_CODE_CHARS]

            arg_names = [arg.arg for arg in node.args.args]
            functions.append(
                FunctionInfo(
                    name=node.name,
                    args=arg_names,
                    code=func_code,
                    lineno=start_line,
                )
            )

    return functions


def find_python_files(repo_path: Path) -> List[Path]:
    """
    Recursively find all .py files inside a repository.
    """
    return [p for p in repo_path.rglob("*.py") if p.is_file()]
