# scripts/dev_tools.py

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_cmd(cmd: list[str]) -> int:
    print(f"\n>>> {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    return proc.returncode


def cmd_format() -> int:
    rc = 0

    # black
    rc = run_cmd([sys.executable, "-m", "black", "app", "scripts", "mcp-servers", "tests"])
    if rc != 0:
        return rc

    # isort
    rc = run_cmd([sys.executable, "-m", "isort", "app", "scripts", "mcp-servers", "tests"])
    if rc != 0:
        return rc

    # ruff --fix (если установлен)
    try:
        rc = run_cmd([sys.executable, "-m", "ruff", "check", "--fix", "app", "scripts", "mcp-servers", "tests"])
    except FileNotFoundError:
        print("ruff не найден, пропускаю авто-фикс.")
        rc = 0

    return rc


def cmd_lint() -> int:
    try:
        return run_cmd([sys.executable, "-m", "ruff", "check", "app", "scripts", "mcp-servers", "tests"])
    except FileNotFoundError:
        print("ruff не найден. Установи его: pip install ruff")
        return 1


def cmd_test() -> int:
    try:
        return run_cmd([sys.executable, "-m", "pytest"])
    except FileNotFoundError:
        print("pytest не найден. Установи его: pip install pytest")
        return 1


def cmd_all() -> int:
    for fn in (cmd_format, cmd_lint, cmd_test):
        rc = fn()
        if rc != 0:
            return rc
    return 0


def main(argv: list[str] | None = None) -> int:

    parser = argparse.ArgumentParser(description="Инструменты разработки DocOps MCP Assistant")
    parser.add_argument(
        "command",
        choices=["format", "lint", "test", "all"],
        help="Что выполнить",
    )

    args = parser.parse_args(argv)

    if args.command == "format":
        return cmd_format()
    if args.command == "lint":
        return cmd_lint()
    if args.command == "test":
        return cmd_test()
    if args.command == "all":
        return cmd_all()

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())