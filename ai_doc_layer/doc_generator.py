from pathlib import Path
from typing import List, Optional
import textwrap

from .code_parser import FunctionInfo
from .llm_client import LLMClient


def sanitize_docstring(raw: str) -> str:
    """
    Cleans LLM output and ensures it becomes a proper, safe docstring.
    """
    if not raw:
        return '"""TODO: add documentation."""'

    text = raw.strip()

    # Remove markdown code blocks
    text = text.replace("```", "").strip()

    # Remove prompt echoes / self-references
    forbidden_phrases = [
        "Write a SHORT Python docstring",
        "Write a short Python docstring",
        "Explain:",
        "Do NOT",
        "Function code:",
        "Function:",
    ]
    for phrase in forbidden_phrases:
        if phrase in text:
            # Keep only first meaningful sentence
            parts = text.split(".")
            text = parts[-1].strip()
    
    # Ensure docstring is short (2–3 sentences max)
    sentences = text.split(".")
    sentences = [s.strip() for s in sentences if s.strip()]
    if len(sentences) > 3:
        sentences = sentences[:3]
    text = ". ".join(sentences)

    # Fallback if empty
    if not text:
        text = "TODO: add documentation."

    return f'"""{text}"""'



class DocGenerator:
    def __init__(self, llm: Optional[LLMClient] = None):
        self.llm = llm or LLMClient()

    def generate_docstring(self, func: FunctionInfo, file_path: Path) -> str:
        prompt = f"""
        Write a short Python docstring (max 2–3 sentences) describing ONLY:

        - What the function does
        - What important parameters mean
        - What it returns (if applicable)

        Do NOT copy these instructions.

        Function:
        {func.code}
        """


        raw = self.llm.generate_with_cache(
            prompt,
            cache_key_extra={"file": file_path.name, "func": func.name},
            extra_params={"max_new_tokens": 70}
        )

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
