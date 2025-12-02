from pathlib import Path
from typing import List, Tuple
from git import Repo, Diff


def get_repo(repo_path: Path) -> Repo:
    return Repo(str(repo_path))


def get_changed_files(repo_path: Path, base: str = "HEAD~1", target: str = "HEAD") -> List[Path]:
    """
    Return list of files changed between two refs (default: last commit vs previous).
    """
    repo = get_repo(repo_path)
    diff_index = repo.commit(base).diff(target)
    files: List[Path] = []

    for d in diff_index:  
        if d.a_path and d.a_path.endswith(".py"):
            files.append(repo_path / d.a_path)
        elif d.b_path and d.b_path.endswith(".py"):
            files.append(repo_path / d.b_path)

    # Deduplicate
    return list({f.resolve() for f in files})


def get_diff_text(repo_path: Path, base: str = "HEAD~1", target: str = "HEAD") -> str:
    """
    Get unified diff text between two refs for context / commit summary.
    """
    repo = get_repo(repo_path)
    return repo.git.diff(base, target)
