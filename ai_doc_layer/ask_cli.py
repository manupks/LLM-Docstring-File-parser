# ask_cli.py
from pathlib import Path
from typing import Optional
from .search_index import SearchIndex
from .llm_client import LLMClient
from .cache import load_from_cache, save_to_cache
from .code_parser import extract_functions_from_file

DEFAULT_TOP_K = 4

class CodebaseAssistant:
    def __init__(self, repo_path: Path, llm: Optional[LLMClient]=None):
        self.repo_path = repo_path
        self.llm = llm or LLMClient()
        self.index = SearchIndex()
        self.index.build_index(repo_path)

    def _build_context(self, query: str, top_k: int = DEFAULT_TOP_K) -> str:
        hits = self.index.query(query, top_k=top_k)
        parts = []
        for (path, name, lineno), score, snippet in hits:
            parts.append(f"File: {path}\nFunction: {name} (line {lineno})\n---\n{snippet}\n---\n")
        context = "\n\n".join(parts)
        return context

    def ask(self, question: str, top_k: int = DEFAULT_TOP_K) -> str:
        # Try cache first
        cache_resp = load_from_cache(question, extra={"top_k": top_k})
        if cache_resp:
            return cache_resp

        context = self._build_context(question, top_k=top_k)
        prompt = (
            "You are an expert developer who only answers based on the provided context.\n"
            "If the answer is not present, say you could not find enough information.\n\n"
            f"Context:\n{context}\n\nQuestion: {question}\nAnswer concisely, cite files/line numbers when relevant."
        )
        # Use small tokens/low temperature for speed
        resp = self.llm.generate(prompt, extra_params={"max_new_tokens": 180, "temperature": 0.1})
        save_to_cache(question, resp, extra={"top_k": top_k})
        return resp
