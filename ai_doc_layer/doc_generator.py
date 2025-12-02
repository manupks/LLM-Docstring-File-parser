from pathlib import Path
from typing import List, Optional
import textwrap

from .code_parser import FunctionInfo
from .llm_client import LLMClient


def sanitize_docstring(raw: str) -> str:
    """
    Convert model output into a safe, minimal triple-quoted docstring.
    """
    if raw is None:
        raw = ""

    raw = str(raw).strip()

    # If model returned code with """...""", keep only the inner content.
    if '"""' in raw:
        parts = raw.split('"""')
        inner_chunks = [parts[i] for i in range(1, len(parts), 2)]
        if inner_chunks:
            raw = inner_chunks[0].strip()

    # Remove markdown fences and backticks (THIS MUST BE ONE LINE)
    raw = raw.replace("```", "").strip()

    # Drop lines that clearly look like code definitions
    cleaned_lines = []
    for ln in raw.splitlines():
        s = ln.strip()
        if s.startswith("def ") or s.startswith("class "):
            continue
        cleaned_lines.append(ln)
    text = "\n".join(cleaned_lines).strip()

    # If still too long, keep only first few lines.
    lines = text.splitlines()
    if len(lines) > 4:
        lines = lines[:4]
    text = "\n".join(lines).strip()

    # Dedent to avoid weird indentation.
    text = textwrap.dedent(text).strip()

    # Remove very generic meta-text if it appears later in the string
    bad_phrases = [
        "valid Python triple-quoted",
        "The output of the function is a valid",
        "The function is designed to be used",
    ]
    for bp in bad_phrases:
        if bp in text and "\n" in text:
            text = text.splitlines()[0].strip()
            break

    # Ensure no inner triple quotes
    text = text.replace('"""', "").strip()

    if not text:
        text = "TODO: add documentation."

    return f'"""{text}"""'


class DocGenerator:
    def __init__(self, llm: Optional[LLMClient] = None):
        self.llm = llm or LLMClient()

    def generate_docstring(self, func: FunctionInfo, file_path: Path) -> str:
        prompt = f"""
You are an expert Python developer.

Write a SHORT docstring for the following function from {file_path.name}.

STRICT RULES:
- Output ONLY a valid Python triple-quoted docstring.
- Do NOT include the function signature.
- Do NOT explain what a docstring is.
- Do NOT mention "valid Python triple-quoted string" or similar.
- Just describe what the function does, its parameters and return value.
- Keep it concise (1–3 sentences).

Function code:
{func.code}
"""
        raw = self.llm.generate(prompt)
        return sanitize_docstring(raw)

    def generate_commit_summary(self, diff_text: str) -> str:
        prompt = f"""
You are a senior engineer.

Given this git diff, write a short human-readable summary of what changed and why it might matter.
Limit to 3-4 bullet points.

Diff:
{diff_text}
"""
        return self.llm.generate(prompt)

    def generate_module_overview(self, file_path: Path, functions: List[FunctionInfo]) -> str:
        func_names = ", ".join([f.name for f in functions]) or "No functions found"
        prompt = f"""
You are documenting a Python module named {file_path.name}.

Functions in this file: {func_names}

Write a short Markdown section explaining:
- What this module is likely responsible for.
- How the main functions work together.
- Any potential entry point for new developers.

Keep it under 8 sentences.
"""
        return self.llm.generate(prompt)
