from pathlib import Path
from typing import Optional

import click

from .code_parser import find_python_files, extract_functions_from_file
from .diff_analyzer import get_changed_files, get_diff_text
from .doc_generator import DocGenerator
from .writer import inject_docstrings_into_file, write_module_markdown
from .uml_generator import generate_repo_uml
from .ask_cli import CodebaseAssistant

@click.group()
def cli():
    """AI Documentation Layer CLI."""
    pass

@cli.command()
@click.argument("repo", type=click.Path(exists=True, file_okay=False))
@click.option("--only-changed", is_flag=True, help="Only process files changed in last commit.")
def generate(repo: str, only_changed: bool):
    """
    Generate documentation for a Python repository.
    """
    repo_path = Path(repo).resolve()
    click.echo(f"Using repo: {repo_path}")

    doc_gen = DocGenerator()

    if only_changed:
        files = get_changed_files(repo_path)
        if not files:
            click.echo("No changed Python files detected between HEAD~1 and HEAD.")
            return
    else:
        files = find_python_files(repo_path)

    click.echo(f"Found {len(files)} Python files to process.")

    for file_path in files:
        click.echo(f"Processing {file_path} ...")
        functions = extract_functions_from_file(file_path)
        if not functions:
            continue

        func_docs = {}
        for func in functions:
            ds = doc_gen.generate_docstring(func, file_path)
            func_docs[func.lineno] = ds

        # Inject docstrings into code (in-place)
        inject_docstrings_into_file(file_path, func_docs)

        # Write module-level Markdown
        module_md = doc_gen.generate_module_overview(file_path, functions)
        write_module_markdown(repo_path, file_path, module_md, functions)

    click.echo("Documentation generation completed.")


@cli.command()
@click.argument("repo", type=click.Path(exists=True, file_okay=False))
def summarize_last_commit(repo: str):
    """
    Summarize the last git commit using LLM.
    """
    repo_path = Path(repo).resolve()
    doc_gen = DocGenerator()
    diff_text = get_diff_text(repo_path)
    summary = doc_gen.generate_commit_summary(diff_text)
    click.echo(summary)

@cli.command()
@click.argument("repo", type=click.Path(exists=True, file_okay=False))
@click.option("--out-dir", type=click.Path(), default=None, help="Where to write diagrams (default: ai_docs/diagrams)")
@click.option("--no-render", is_flag=True, help="Do not render PNGs (only write DOT files).")
def generate_uml(repo: str, out_dir: Optional[str], no_render: bool):
    """Generate UML diagrams (DOT + PNG) for each module in the repo."""
    repo_path = Path(repo).resolve()
    docs_root = repo_path / "ai_docs"
    out = Path(out_dir).resolve() if out_dir else docs_root / "diagrams"
    click.echo(f"Generating UML diagrams into {out} ...")
    generate_repo_uml(repo_path, out, render_png=(not no_render))
    click.echo("UML generation completed.")

@cli.command()
@click.argument("repo", type=click.Path(exists=True, file_okay=False))
@click.argument("question", type=str)
@click.option("--top-k", type=int, default=4, help="How many top snippets to include in context.")
def ask(repo: str, question: str, top_k: int):
    """Query the codebase using the LLM + local retrieval."""
    repo_path = Path(repo).resolve()
    click.echo(f"Asking against {repo_path}: {question}")
    assistant = CodebaseAssistant(repo_path)
    resp = assistant.ask(question, top_k=top_k)
    click.echo("\n---- Answer ----\n")
    click.echo(resp)