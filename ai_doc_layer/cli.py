from pathlib import Path
from typing import Optional

import click

from .code_parser import find_python_files, extract_functions_from_file
from .diff_analyzer import get_changed_files, get_diff_text
from .doc_generator import DocGenerator
from .writer import inject_docstrings_into_file, write_module_markdown


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
