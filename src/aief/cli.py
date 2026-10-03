"""Command line: `aief check` (conformance to the standards) and `aief intake` (use-case triage)."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from . import __version__, intake, standards

STATUS = {"pass": "pass", "fail": "FAIL", "n/a": "n/a", "waived": "waived"}


def _table(findings: list[standards.Finding]) -> str:
    rows = [f"{'Rule':<7} {'Level':<6} {'Status':<6} {'Standard':<46} Detail"]
    for f in findings:
        rows.append(f"{f.rule:<7} {f.level:<6} {STATUS[f.status]:<6} {f.title:<46} {f.detail}")
    return "\n".join(rows)


def _markdown(name: str, findings: list[standards.Finding]) -> str:
    lines = [f"### {name}", "", "| Rule | Level | Status | Standard | Detail |"]
    lines.append("|---|---|---|---|---|")
    for f in findings:
        lines.append(f"| {f.rule} | {f.level} | {STATUS[f.status]} | {f.title} | {f.detail} |")
    return "\n".join(lines)


def _summary(findings: list[standards.Finding]) -> str:
    counted = [f for f in findings if f.status in {"pass", "fail"}]
    must = [f for f in counted if f.level == "MUST"]
    should = [f for f in counted if f.level == "SHOULD"]
    waived = sum(f.status == "waived" for f in findings)

    def ok(xs: list[standards.Finding]) -> int:
        return sum(f.status == "pass" for f in xs)

    text = f"MUST {ok(must)}/{len(must)}, SHOULD {ok(should)}/{len(should)}"
    return text + (f", {waived} waived" if waived else "")


def cmd_check(args: argparse.Namespace) -> int:
    exit_code = 0
    for path in args.paths:
        root = Path(path)
        findings = standards.check(root)
        good = standards.passed(findings, strict=args.strict)
        exit_code |= 0 if good else 1
        name = root.resolve().name
        if args.format == "json":
            print(
                json.dumps(
                    {"repo": name, "passed": good, "findings": [asdict(f) for f in findings]},
                    indent=2,
                )
            )
        elif args.format == "md":
            print(_markdown(name, findings) + f"\n\n{_summary(findings)}\n")
        else:
            print(f"{name}: {_summary(findings)} -> {'conforms' if good else 'does not conform'}")
            print(_table(findings) + "\n")
    return exit_code


def cmd_intake(args: argparse.Namespace) -> int:
    try:
        assessment = intake.assess(intake.load(Path(args.file)))
    except (intake.IntakeError, OSError) as exc:
        print(f"intake error: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(assessment.to_dict(), indent=2))
    else:
        print(intake.to_markdown(assessment), end="")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="aief", description=__doc__)
    parser.add_argument("--version", action="version", version=f"aief {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("check", help="check repositories against the engineering standards")
    p.add_argument("paths", nargs="+", help="repository folders")
    p.add_argument("--format", choices=["table", "md", "json"], default="table")
    p.add_argument("--strict", action="store_true", help="SHOULD rules also fail the check")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("intake", help="score a use-case intake file (YAML or JSON)")
    p.add_argument("file")
    p.add_argument("--format", choices=["md", "json"], default="md")
    p.set_defaults(func=cmd_intake)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
