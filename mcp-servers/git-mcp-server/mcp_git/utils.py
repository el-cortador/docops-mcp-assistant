# mcp-servers/git-mcp-server/mcp_git/utils.py
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Tuple, Optional


def get_required_env(name: str, default: Optional[str] = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(
            f"Environment variable {name} is not set and no default was provided."
        )
    return value


def run_git_command(
    args: list[str],
    cwd: Path,
    check: bool = True,
) -> str:
    process = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if check and process.returncode != 0:
        raise RuntimeError(
            f"git command failed (exit {process.returncode}): "
            f"{process.stderr.strip()}"
        )

    return process.stdout


def get_demo_repos_dir() -> Path:
    env_path = os.getenv("DOCOPS_DEMO_REPOS_DIR")
    if env_path:
        return Path(env_path).expanduser().resolve()

    root = Path(__file__).resolve().parents[3]
    return root / "demo_data" / "demo_repos"


def parse_github_repo_url(url: str) -> Tuple[str, str]:
    cleaned = url.strip()

    if cleaned.startswith("git@github.com:"):
        cleaned = cleaned[len("git@github.com:") :]
    elif "github.com/" in cleaned:
        idx = cleaned.index("github.com/")
        cleaned = cleaned[idx + len("github.com/") :]

    cleaned = cleaned.rstrip("/")
    if cleaned.endswith(".git"):
        cleaned = cleaned[: -len(".git")]

    parts = cleaned.split("/")
    if len(parts) < 2:
        raise ValueError(
            f"Could not parse GitHub repo URL '{url}'. "
            "Expected something like 'owner/repo' or full GitHub URL."
        )

    owner, repo = parts[0], parts[1]
    return owner, repo