"""The engineering standards, as checks that run against a repository.

Each standard in docs/standards.md that can be checked from the files alone is a `Rule` here.
The checks are deliberately simple and explainable: they look for evidence that a practice is
in place (a workflow step, a file, a pinned version), not for proof that it is done well. A
review still decides that. What the check gives is a cheap, consistent floor, run in CI, so no
service reaches review without its tests, its evaluation, its operating notes and a local path.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".mypy_cache",
    ".tox",
    ".idea",
    ".vscode",
}
TEXT_SUFFIXES = {
    ".py",
    ".md",
    ".txt",
    ".toml",
    ".yml",
    ".yaml",
    ".json",
    ".jsonl",
    ".cfg",
    ".ini",
    ".env",
    ".sh",
    ".ps1",
    ".js",
    ".ts",
    ".html",
    ".dockerfile",
    "",
}
MAX_SCAN_BYTES = 512_000

# Secret patterns: specific enough to avoid noise on documentation such as "sk-ant-...".
SECRET_PATTERNS = {
    "Anthropic API key": re.compile(r"sk-ant-[A-Za-z0-9_\-]{30,}"),
    "OpenAI-style API key": re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9]{32,}"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
    "Private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "Azure storage key": re.compile(r"AccountKey=[A-Za-z0-9+/]{60,}={0,2}"),
}
LOCAL_RUNTIME = re.compile(
    r"\b(ollama|vllm|llama\.cpp|llama-cpp|lm studio|localai|open-weight|openai-compatible|"
    r"openai compatible|local model|runs offline|no api key)\b",
    re.IGNORECASE,
)
COMMAND_HINT = re.compile(
    r"\b(pytest|ruff|npm (run|test)|make \w+|go test|cargo test|docker compose|tox|nox)\b"
    r"|```(bash|sh|shell|powershell)",
    re.IGNORECASE,
)
SCANNERS = re.compile(r"\b(pip-audit|safety check|osv-scanner|trivy|grype|codeql)\b", re.I)


@dataclass
class Finding:
    rule: str
    title: str
    level: str  # MUST or SHOULD
    status: str  # pass, fail, n/a, waived
    detail: str


@dataclass
class Rule:
    id: str
    title: str
    level: str
    check: Callable[[Repo], tuple[str, str]]


class Repo:
    """Read-only view of a repository on disk, with the lookups the rules need."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        if not self.root.is_dir():
            raise NotADirectoryError(f"not a directory: {root}")
        self._files = sorted(self._walk(self.root))

    def _walk(self, folder: Path) -> Iterator[Path]:
        for path in folder.iterdir():
            if path.is_dir():
                if path.name not in SKIP_DIRS and not path.name.endswith(".egg-info"):
                    yield from self._walk(path)
            elif path.is_file():
                yield path

    @property
    def files(self) -> list[Path]:
        return self._files

    def rel(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def find(self, pattern: str) -> list[Path]:
        """Files whose path relative to the root matches a regular expression."""
        rx = re.compile(pattern, re.IGNORECASE)
        return [p for p in self._files if rx.search(self.rel(p))]

    def read(self, path: Path) -> str:
        try:
            if path.stat().st_size > MAX_SCAN_BYTES:
                return ""
            return path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return ""

    def workflows(self) -> str:
        return "\n".join(self.read(p) for p in self.find(r"^\.github/workflows/.+\.ya?ml$"))

    def text_files(self) -> Iterator[Path]:
        for p in self._files:
            if p.suffix.lower() in TEXT_SUFFIXES or p.name in {"Dockerfile", "Containerfile"}:
                yield p


# Rules -------------------------------------------------------------------------------------


def _readme(repo: Repo):
    found = repo.find(r"^readme\.(md|rst|txt)$")
    if not found:
        return "fail", "no README at the root"
    text = repo.read(found[0]).lower()
    if not re.search(r"quick ?start|getting started|how to run|## (install|usage|run)", text):
        return "fail", "README has no quick start or run instructions"
    return "pass", found[0].name


def _license(repo: Repo):
    found = repo.find(r"^(licen[cs]e|copying)(\.\w+)?$")
    return ("pass", found[0].name) if found else ("fail", "no LICENSE file")


def _tests(repo: Repo):
    found = repo.find(r"(^|/)tests?/(.+/)?test_[^/]+\.py$")
    if found:
        return "pass", f"{len(found)} test files"
    smoke = repo.find(r"^scripts/.*(smoke|e2e|end_to_end).*\.py$")
    if smoke:
        return "pass", f"end-to-end test: {repo.rel(smoke[0])}"
    return "fail", "no tests/test_*.py or end-to-end test script"


def _ci(repo: Repo):
    found = repo.find(r"^\.github/workflows/.+\.ya?ml$")
    if not found:
        return "fail", "no workflow in .github/workflows"
    if not re.search(r"\bpytest\b|\bnpm test\b|\bgo test\b|smoke_test|e2e", repo.workflows()):
        return "fail", "CI does not run the tests"
    return "pass", ", ".join(repo.rel(p) for p in found)


def _evals(repo: Repo):
    found = repo.find(r"^evals?/.+\.(jsonl|json|ya?ml|csv)$")
    return ("pass", f"{len(found)} evaluation files") if found else ("fail", "no evals/ data")


def _eval_gate(repo: Repo):
    if not repo.find(r"^evals?/"):
        return "n/a", "no evaluation set"
    if re.search(r"\beval(uate|uation)?\b", repo.workflows(), re.IGNORECASE):
        return "pass", "CI runs the evaluation"
    return "fail", "evaluation exists but CI does not run it"


def _decisions(repo: Repo):
    found = repo.find(r"^docs/(.*decision.*|adr/.+)\.md$")
    return ("pass", repo.rel(found[0])) if found else ("fail", "no docs/*decisions*.md or ADRs")


def _bounded_deps(repo: Repo):
    pyproject = repo.root / "pyproject.toml"
    if not pyproject.exists():
        return "n/a", "no pyproject.toml"
    text = repo.read(pyproject)
    block = re.search(r"^dependencies\s*=\s*\[(.*?)\]", text, re.S | re.M)
    if not block:
        return "pass", "no runtime dependencies"
    deps = re.findall(r"\"([^\"]+)\"", block.group(1))
    loose = [d for d in deps if not re.search(r"[<>=~!]", d)]
    if loose:
        return "fail", "unversioned: " + ", ".join(loose)
    return "pass", f"{len(deps)} runtime dependencies, all versioned"


def _non_root(repo: Repo):
    files = repo.find(r"(^|/)(Dockerfile|Containerfile)[^/]*$")
    if not files:
        return "n/a", "no container image"
    bad = []
    for f in files:
        users = re.findall(r"^\s*USER\s+(\S+)", repo.read(f), re.M)
        if not users or users[-1] in {"root", "0", "0:0"}:
            bad.append(repo.rel(f))
    return ("fail", "runs as root: " + ", ".join(bad)) if bad else ("pass", "non-root USER set")


def _dependabot(repo: Repo):
    found = repo.find(r"^\.github/(dependabot\.ya?ml|renovate\.json)$") or repo.find(
        r"^renovate\.json$"
    )
    return ("pass", repo.rel(found[0])) if found else ("fail", "no Dependabot or Renovate config")


def _vuln_scan(repo: Repo):
    m = SCANNERS.search(repo.workflows())
    return ("pass", f"CI runs {m.group(1)}") if m else ("fail", "no dependency scan in CI")


def _secrets(repo: Repo):
    hits = []
    for p in repo.text_files():
        if p.name == ".env":
            hits.append(f"{repo.rel(p)} (committed .env file)")
            continue
        text = repo.read(p)
        for label, rx in SECRET_PATTERNS.items():
            if rx.search(text):
                hits.append(f"{repo.rel(p)} ({label})")
    return ("fail", "; ".join(hits[:5])) if hits else ("pass", "no secret patterns found")


def _local_path(repo: Repo):
    docs = [p for p in repo.find(r"\.md$") if not repo.rel(p).startswith("tests/")]
    for p in docs:
        m = LOCAL_RUNTIME.search(repo.read(p))
        if m:
            return "pass", f"{repo.rel(p)} mentions '{m.group(1)}'"
    return "fail", "no documented way to run without a commercial API"


def _operations(repo: Repo):
    found = repo.find(r"^(operations\.md|runbook\.md|docs/(operations|runbook|lifecycle)\.md)$")
    return ("pass", repo.rel(found[0])) if found else ("fail", "no OPERATIONS.md or runbook")


def _system_card(repo: Repo):
    found = repo.find(r"^(system_card\.md|model_card\.md|docs/(system|model)[-_]card\.md)$")
    return ("pass", repo.rel(found[0])) if found else ("fail", "no SYSTEM_CARD.md")


def _agent_context(repo: Repo):
    """A root context file for coding agents, naming at least one command to run.

    Coding agents read Markdown context files at the repository root before they work
    (AGENTS.md is the shared convention; CLAUDE.md is read by Claude Code and can import
    AGENTS.md). Without one, every agent rediscovers the commands and, worse, the invariants
    nobody may weaken. The check wants the file and a runnable command in it.
    """
    found = repo.find(r"^(agents|claude)\.md$")
    if not found:
        return "fail", "no AGENTS.md (or CLAUDE.md) at the root"
    for path in found:
        if COMMAND_HINT.search(repo.read(path)):
            return "pass", path.name
    return "fail", f"{found[0].name} names no command to run (tests, lint, evaluation)"


def _changelog(repo: Repo):
    found = repo.find(r"^(changelog|history|releases)\.md$")
    return ("pass", found[0].name) if found else ("fail", "no CHANGELOG.md")


RULES: list[Rule] = [
    Rule("ENG-01", "README with a quick start", "MUST", _readme),
    Rule("ENG-02", "Automated tests", "MUST", _tests),
    Rule("ENG-03", "CI runs the tests", "MUST", _ci),
    Rule("ENG-04", "No secrets in the repository", "MUST", _secrets),
    Rule("ENG-05", "Evaluation set", "MUST", _evals),
    Rule("ENG-06", "CI runs the evaluation as a gate", "MUST", _eval_gate),
    Rule("ENG-07", "Runtime dependencies versioned", "MUST", _bounded_deps),
    Rule("ENG-08", "Containers run as a non-root user", "MUST", _non_root),
    Rule("ENG-09", "Runs without a commercial API (local path)", "SHOULD", _local_path),
    Rule("ENG-10", "Design decisions recorded", "SHOULD", _decisions),
    Rule("ENG-11", "Operating notes (OPERATIONS.md / runbook)", "SHOULD", _operations),
    Rule("ENG-12", "System card (intended use, limits, oversight)", "SHOULD", _system_card),
    Rule("ENG-13", "Dependency updates automated", "SHOULD", _dependabot),
    Rule("ENG-14", "Dependency vulnerability scan in CI", "SHOULD", _vuln_scan),
    Rule("ENG-15", "Changelog", "SHOULD", _changelog),
    Rule("ENG-16", "Licence", "SHOULD", _license),
    Rule("ENG-17", "Context file for coding agents (AGENTS.md)", "SHOULD", _agent_context),
]


def waivers(root: Path) -> dict[str, str]:
    """Recorded exceptions: `[tool.aief.waivers]` in pyproject.toml maps a rule id to a reason.

    A waiver is visible in every report with its reason, so an exception is a decision someone
    wrote down rather than a silent gap.
    """
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return {}
    try:
        import tomllib
    except ModuleNotFoundError:  # Python 3.10
        import tomli as tomllib  # type: ignore[no-redef]
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, OSError):
        return {}
    table = data.get("tool", {}).get("aief", {}).get("waivers", {})
    return {str(k): str(v) for k, v in table.items() if str(v).strip()}


def check(root: Path, rules: list[Rule] | None = None) -> list[Finding]:
    repo = Repo(root)
    waived = waivers(repo.root)
    findings = []
    for rule in rules or RULES:
        status, detail = rule.check(repo)
        if status == "fail" and rule.id in waived:
            status, detail = "waived", waived[rule.id]
        findings.append(Finding(rule.id, rule.title, rule.level, status, detail))
    return findings


def passed(findings: list[Finding], strict: bool = False) -> bool:
    """MUST rules must pass; with strict, SHOULD rules too. 'n/a' and 'waived' never fail."""
    levels = {"MUST", "SHOULD"} if strict else {"MUST"}
    return not any(f.status == "fail" and f.level in levels for f in findings)
