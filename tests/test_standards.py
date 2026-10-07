from pathlib import Path

from aief import standards
from aief.cli import main


def write(root: Path, rel: str, text: str = "") -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def good_repo(root: Path) -> Path:
    write(root, "README.md", "# svc\n\n## Quick start\n\nRuns offline with Ollama.\n")
    write(root, "LICENSE", "MIT")
    write(root, "tests/test_core.py", "def test_ok():\n    assert True\n")
    write(
        root,
        ".github/workflows/ci.yml",
        "jobs:\n  t:\n    steps:\n      - run: pytest\n      - run: svc eval evals/cases.jsonl\n"
        "      - run: pip-audit\n",
    )
    write(root, ".github/dependabot.yml", "version: 2\n")
    write(root, "evals/cases.jsonl", '{"q": "x"}\n')
    write(root, "docs/decisions.md", "# Decisions\n")
    write(root, "OPERATIONS.md", "# Operations\n")
    write(root, "SYSTEM_CARD.md", "# System card\n")
    write(root, "CHANGELOG.md", "# Changelog\n")
    write(root, "pyproject.toml", '[project]\ndependencies = [\n    "httpx>=0.27,<1",\n]\n')
    write(root, "Dockerfile", "FROM python:3.12-slim\nUSER appuser\n")
    write(root, "AGENTS.md", "# Agents\n\n```bash\npytest\n```\n")
    return root


def by_rule(findings):
    return {f.rule: f for f in findings}


def test_good_repo_passes_every_rule(tmp_path):
    findings = standards.check(good_repo(tmp_path))
    failing = [f for f in findings if f.status != "pass"]
    assert failing == []
    assert standards.passed(findings, strict=True)


def test_empty_repo_fails_must_rules(tmp_path):
    findings = by_rule(standards.check(tmp_path))
    assert findings["ENG-01"].status == "fail"
    assert findings["ENG-02"].status == "fail"
    assert findings["ENG-06"].status == "n/a"  # no evaluation set, so no gate to check
    assert findings["ENG-08"].status == "n/a"  # no container image
    assert not standards.passed(list(findings.values()))


def test_secret_is_detected_and_documentation_placeholder_is_not(tmp_path):
    good_repo(tmp_path)
    write(tmp_path, "docs/setup.md", "export ANTHROPIC_API_KEY=sk-ant-...\n")
    assert by_rule(standards.check(tmp_path))["ENG-04"].status == "pass"
    write(tmp_path, "src/config.py", 'KEY = "sk-ant-api03-' + "a" * 40 + '"\n')
    finding = by_rule(standards.check(tmp_path))["ENG-04"]
    assert finding.status == "fail"
    assert "src/config.py" in finding.detail


def test_committed_env_file_fails(tmp_path):
    good_repo(tmp_path)
    write(tmp_path, ".env", "TOKEN=abc\n")
    assert by_rule(standards.check(tmp_path))["ENG-04"].status == "fail"


def test_root_container_and_unversioned_dependency_fail(tmp_path):
    good_repo(tmp_path)
    write(tmp_path, "Dockerfile", "FROM python:3.12-slim\n")
    write(tmp_path, "pyproject.toml", '[project]\ndependencies = ["httpx", "pyyaml>=6"]\n')
    findings = by_rule(standards.check(tmp_path))
    assert findings["ENG-08"].status == "fail"
    assert findings["ENG-07"].status == "fail"
    assert "httpx" in findings["ENG-07"].detail


def test_evaluation_not_in_ci_fails_gate(tmp_path):
    good_repo(tmp_path)
    write(tmp_path, ".github/workflows/ci.yml", "jobs:\n  t:\n    steps:\n      - run: pytest\n")
    assert by_rule(standards.check(tmp_path))["ENG-06"].status == "fail"


def test_local_path_rule(tmp_path):
    good_repo(tmp_path)
    write(tmp_path, "README.md", "# svc\n\n## Quick start\n\nSet ANTHROPIC_API_KEY.\n")
    assert by_rule(standards.check(tmp_path))["ENG-09"].status == "fail"


def test_waiver_is_reported_with_its_reason(tmp_path):
    good_repo(tmp_path)
    (tmp_path / "SYSTEM_CARD.md").unlink()
    write(
        tmp_path,
        "pyproject.toml",
        "[project]\ndependencies = []\n\n[tool.aief.waivers]\n"
        'ENG-12 = "Platform only: each component has its own system card"\n',
    )
    finding = by_rule(standards.check(tmp_path))["ENG-12"]
    assert finding.status == "waived"
    assert "own system card" in finding.detail
    assert standards.passed(standards.check(tmp_path), strict=True)


def test_end_to_end_script_counts_as_tests(tmp_path):
    write(tmp_path, "scripts/smoke_test.py", "print('ok')\n")
    write(tmp_path, ".github/workflows/ci.yml", "steps:\n  - run: python scripts/smoke_test.py\n")
    findings = by_rule(standards.check(tmp_path))
    assert findings["ENG-02"].status == "pass"
    assert findings["ENG-03"].status == "pass"


def test_cli_exit_codes(tmp_path, capsys):
    assert main(["check", str(good_repo(tmp_path / "good"))]) == 0
    (tmp_path / "bad").mkdir()
    assert main(["check", str(tmp_path / "bad")]) == 1
    assert main(["check", "--format", "md", str(tmp_path / "good")]) == 0
    assert "| ENG-01 |" in capsys.readouterr().out


def test_agent_context_file_needs_a_command(tmp_path):
    good_repo(tmp_path)
    assert by_rule(standards.check(tmp_path))["ENG-17"].status == "pass"
    write(tmp_path, "AGENTS.md", "# Agents\n\nBe careful.\n")
    finding = by_rule(standards.check(tmp_path))["ENG-17"]
    assert finding.status == "fail"
    assert "names no command" in finding.detail
    (tmp_path / "AGENTS.md").unlink()
    write(tmp_path, "CLAUDE.md", "@AGENTS.md\n\nRun `pytest` before committing.\n")
    assert by_rule(standards.check(tmp_path))["ENG-17"].status == "pass"
    (tmp_path / "CLAUDE.md").unlink()
    finding = by_rule(standards.check(tmp_path))["ENG-17"]
    assert finding.status == "fail"
    assert standards.passed([finding])  # a SHOULD rule: fails only under --strict
    assert not standards.passed([finding], strict=True)
