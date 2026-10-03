"""The service template renders, compiles and meets the standards it is meant to demonstrate.

The generated project's own tests and evaluation run in CI (job `template`), where its
dependencies are installed.
"""

import py_compile
import re
import shutil
from pathlib import Path

import pytest

from aief import standards

copier = pytest.importorskip("copier")
ROOT = Path(__file__).resolve().parent.parent
IGNORE = shutil.ignore_patterns(".git", ".venv", "__pycache__", "*.egg-info", ".pytest_cache")


def render(tmp_path: Path, **answers) -> Path:
    # Copy first, so the working tree is rendered (not the last git tag).
    src = tmp_path / "src"
    shutil.copytree(ROOT, src, ignore=IGNORE)
    dst = tmp_path / "out"
    copier.run_copy(str(src), str(dst), data=answers, defaults=True, unsafe=True, quiet=True)
    return dst


def test_default_render(tmp_path):
    out = render(tmp_path)
    for rel in [
        "README.md",
        "OPERATIONS.md",
        "SYSTEM_CARD.md",
        "THREAT_MODEL.md",
        "Dockerfile",
        "compose.yaml",
        ".github/workflows/ci.yml",
        "evals/cases.jsonl",
        "src/policy_answers/service.py",
        "tests/test_service.py",
        ".copier-answers.yml",
    ]:
        assert (out / rel).is_file(), rel


def test_no_unrendered_template_syntax(tmp_path):
    out = render(tmp_path, project_name="Staff Help Desk", classification_ceiling="restricted")
    for path in out.rglob("*"):
        if path.is_file() and path.suffix in {".py", ".toml", ".md", ".yml", ".yaml", ".jsonl"}:
            text = path.read_text(encoding="utf-8")
            # GitHub Actions expressions (${{ ... }}) are expected in workflows.
            leftovers = re.findall(r"(?<!\$)\{\{|\{%", text)
            assert not leftovers, path
            assert not path.name.endswith(".jinja")


def test_generated_python_compiles(tmp_path):
    out = render(tmp_path)
    for path in out.rglob("*.py"):
        py_compile.compile(str(path), doraise=True)


def test_answers_flow_into_the_service(tmp_path):
    out = render(
        tmp_path,
        project_name="Staff Help Desk",
        local_model="qwen2.5:7b",
        classification_ceiling="restricted",
    )
    config = (out / "src/staff_help_desk/config.py").read_text(encoding="utf-8")
    assert 'model_name: str = "qwen2.5:7b"' in config
    assert 'max_classification: str = "restricted"' in config
    # At a restricted ceiling the board document is readable, so its "withheld" case is dropped.
    assert "withheld-document" not in (out / "evals/cases.jsonl").read_text(encoding="utf-8")
    assert "staff-help-desk = " in (out / "pyproject.toml").read_text(encoding="utf-8")


def test_generated_project_meets_the_standards(tmp_path):
    findings = standards.check(render(tmp_path))
    problems = [f"{f.rule} {f.detail}" for f in findings if f.status == "fail"]
    assert problems == []
    assert standards.passed(findings, strict=True)
