import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from repo_scout.cli import main, scan_repository


class ScanRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def make_ready_repository(self):
        (self.root / ".git").mkdir()
        (self.root / "README.md").write_text("# Example\n", encoding="utf-8")
        (self.root / "LICENSE").write_text("MIT\n", encoding="utf-8")
        (self.root / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
        (self.root / ".github" / "workflows").mkdir(parents=True)
        (self.root / ".github" / "workflows" / "ci.yaml").write_text("name: CI\n", encoding="utf-8")
        (self.root / "tests").mkdir()
        (self.root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")

    def test_all_markers_pass(self):
        self.make_ready_repository()

        findings = scan_repository(self.root)

        self.assertEqual(len(findings), 7)
        self.assertTrue(all(item.status == "pass" for item in findings))

    def test_empty_readme_fails(self):
        (self.root / "README.md").write_text(" \n", encoding="utf-8")

        finding = next(item for item in scan_repository(self.root) if item.key == "readme")

        self.assertEqual(finding.status, "fail")
        self.assertIsNotNone(finding.suggestion)

    def test_readme_directory_does_not_crash(self):
        (self.root / "README.md").mkdir()

        finding = next(item for item in scan_repository(self.root) if item.key == "readme")

        self.assertEqual(finding.status, "fail")

    def test_worktree_git_file_counts_as_repository(self):
        (self.root / ".git").write_text("gitdir: ../.git/worktrees/example\n", encoding="utf-8")

        finding = next(item for item in scan_repository(self.root) if item.key == "git")

        self.assertEqual(finding.status, "pass")

    def test_missing_project_markers_are_actionable(self):
        findings = scan_repository(self.root)

        self.assertTrue(all(item.suggestion for item in findings if item.status != "pass"))


class CommandLineTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_json_output_contains_findings(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = main([str(self.root), "--format", "json"])

        result = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(result["path"], str(self.root.resolve()))
        self.assertEqual(len(result["findings"]), 7)

    def test_strict_mode_fails_when_findings_need_attention(self):
        with contextlib.redirect_stdout(io.StringIO()):
            exit_code = main([str(self.root), "--strict"])

        self.assertEqual(exit_code, 1)

    def test_non_strict_mode_allows_incomplete_repository(self):
        with contextlib.redirect_stdout(io.StringIO()):
            exit_code = main([str(self.root)])

        self.assertEqual(exit_code, 0)

    def test_invalid_path_returns_status_two(self):
        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            exit_code = main([str(self.root / "missing")])

        self.assertEqual(exit_code, 2)
        self.assertIn("not a directory", error.getvalue())

    def test_file_path_returns_status_two(self):
        file_path = self.root / "file.txt"
        file_path.write_text("content", encoding="utf-8")
        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            exit_code = main([str(file_path)])

        self.assertEqual(exit_code, 2)


if __name__ == "__main__":
    unittest.main()
