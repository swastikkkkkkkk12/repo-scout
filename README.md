# Repo Scout

Repo Scout is a read-only command-line checklist for common repository sharing and contribution signals. It scans a local project, explains missing markers, and can emit JSON for scripts and dashboards. It uses only the Python standard library at runtime.

## What it checks

| Check | Passing signal |
| --- | --- |
| Git repository | A `.git` directory or worktree file exists |
| Project README | A non-empty `README`, `README.md`, `README.rst`, or `README.txt` exists |
| License | A common `LICENSE` or `COPYING` file exists |
| Git ignore rules | `.gitignore` exists |
| Continuous integration | A `.yml` or `.yaml` workflow exists under `.github/workflows` |
| Test structure | A conventional test directory or common test filename exists |
| Build metadata | A recognized language manifest exists |

These are marker checks, not content audits. A passing result does not establish that a workflow succeeds, tests are meaningful, a license is legally appropriate, or a repository is secure or high quality.

## Requirements

- Python 3.10 or newer

## Install

Install the checked out project:

```bash
python -m pip install .
```

Or run directly from the checkout without installing:

```bash
PYTHONPATH=src python -m repo_scout.cli .
```

## Use

```bash
repo-scout .
repo-scout ~/code/my-project
repo-scout . --format json
repo-scout . --strict
repo-scout --version
```

Text output is intended for people. JSON output contains the absolute scanned path and an ordered `findings` array. Each finding has a stable key, status (`pass`, `warn`, or `fail`), title, detail, and optional suggestion.

Exit codes:

| Code | Meaning |
| --- | --- |
| `0` | Scan completed; with `--strict`, every check passed |
| `1` | Scan completed, but at least one check needs attention in `--strict` mode |
| `2` | The supplied path does not exist or is not a directory |

Without `--strict`, completed scans return `0` even when checks have warnings or failures. Repo Scout never modifies the scanned project.

## Development

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

The GitHub Actions workflow installs the package, runs the test suite and strict scan, and compiles the source across Python 3.10 through 3.14.

## Contributing

Issues and pull requests are welcome. Keep scans read-only, make each heuristic understandable, and add tests for behavior changes. The runtime has no third-party dependencies.

## License

MIT. See [LICENSE](LICENSE).
