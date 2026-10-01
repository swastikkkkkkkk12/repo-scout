"""Command-line interface for Repo Scout."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from . import __version__


@dataclass(frozen=True)
class Finding:
    key: str
    status: str
    title: str
    detail: str
    suggestion: str | None = None


def _has_any(root: Path, names: Iterable[str]) -> bool:
    return any((root / name).is_file() for name in names)


def scan_repository(root: Path) -> list[Finding]:
    """Inspect common repository hygiene signals without changing files."""
    root = root.expanduser().resolve()
    findings: list[Finding] = []

    has_git = (root / ".git").exists()
    findings.append(Finding(
        "git", "pass" if has_git else "warn",
        "Git repository", "Git metadata found." if has_git else "No .git metadata found.",
        None if has_git else "Initialize Git if this project is intended to be version controlled.",
    ))

    readme_names = ("README.md", "README.rst", "README.txt", "README")
    readme_path = next((root / name for name in readme_names if (root / name).is_file()), None)
    readme = readme_path is not None and bool(readme_path.read_text(encoding="utf-8", errors="replace").strip())
    findings.append(Finding(
        "readme", "pass" if readme else "fail", "Project README",
        "A README file is present." if readme else "No common README file found.",
        None if readme else "Add setup instructions, a short description, and one usage example.",
    ))

    license_file = _has_any(root, ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"))
    findings.append(Finding(
        "license", "pass" if license_file else "warn", "License",
        "A license file is present." if license_file else "No common license file found.",
        None if license_file else "Choose a license that matches how you want others to use the project.",
    ))

    gitignore = (root / ".gitignore").is_file()
    findings.append(Finding(
        "gitignore", "pass" if gitignore else "warn", "Git ignore rules",
        ".gitignore is present." if gitignore else "No .gitignore file found.",
        None if gitignore else "Ignore generated files, local environments, and secrets appropriate to your stack.",
    ))

    workflows = root / ".github" / "workflows"
    ci = workflows.is_dir() and (any(workflows.glob("*.yml")) or any(workflows.glob("*.yaml")))
    findings.append(Finding(
        "ci", "pass" if ci else "warn", "Continuous integration",
        "A GitHub Actions workflow is present." if ci else "No GitHub Actions workflow found.",
        None if ci else "Add CI that installs dependencies and runs the project's checks on each change.",
    ))

    test_markers = ("tests", "test", "spec", "specs")
    tests = any((root / marker).is_dir() for marker in test_markers)
    if not tests:
        tests = any(root.glob("test_*.py")) or any(root.glob("*.test.*")) or any(root.glob("*.spec.*"))
    findings.append(Finding(
        "tests", "pass" if tests else "warn", "Test structure",
        "A conventional test directory or test file is present." if tests else "No conventional test directory or test file found.",
        None if tests else "Add a small test suite for core behavior and document how to run it.",
    ))

    package_metadata = _has_any(root, ("pyproject.toml", "package.json", "Cargo.toml", "go.mod", "pom.xml", "build.gradle", "build.gradle.kts", "Gemfile"))
    findings.append(Finding(
        "metadata", "pass" if package_metadata else "warn", "Build or package metadata",
        "A common language or package manifest is present." if package_metadata else "No recognized package manifest found.",
        None if package_metadata else "Add the manifest for your language so contributors can install and run the project.",
    ))

    return findings


def _render_text(root: Path, findings: list[Finding]) -> str:
    icons = {"pass": "[OK]", "warn": "[WARN]", "fail": "[TODO]"}
    lines = [f"Repo Scout — {root}", ""]
    for item in findings:
        lines.append(f"{icons[item.status]} {item.title}: {item.detail}")
        if item.suggestion:
            lines.append(f"     Try: {item.suggestion}")
    passed = sum(item.status == "pass" for item in findings)
    lines.extend(("", f"Score: {passed}/{len(findings)} checks present"))
    lines.append("This checklist is a starting point; it does not assess code quality or security.")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo-scout",
        description="Check common repository readiness signals without changing files.",
    )
    parser.add_argument("path", nargs="?", default=".", help="repository directory to inspect (default: current directory)")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="output format")
    parser.add_argument("--strict", action="store_true", help="exit with status 1 if any check is not passing")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    root = Path(args.path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        print(f"repo-scout: not a directory: {root}", file=sys.stderr)
        return 2

    findings = scan_repository(root)
    if args.format == "json":
        print(json.dumps({"path": str(root), "findings": [asdict(item) for item in findings]}, indent=2))
    else:
        print(_render_text(root, findings))

    if args.strict and any(item.status != "pass" for item in findings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
