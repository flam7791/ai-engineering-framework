"""Load approved documents and split them into citable passages.

Documents are Markdown files with a small front matter block:

    ---
    id: POL-001
    title: Use of AI tools
    classification: public
    owner: Digital Office
    ---

Each `## ` section becomes one passage, cited as `POL-001#2`. A document without an id or a
valid classification is refused at load time: an unlabelled document is not "probably fine".
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .config import LEVELS


class DocumentError(ValueError):
    pass


@dataclass(frozen=True)
class Passage:
    id: str  # DOC-ID#n
    doc_id: str
    title: str
    heading: str
    text: str
    classification: str
    source: str  # file path, for the audit trail


def parse(path: Path, root: Path) -> list[Passage]:
    raw = path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw, re.S)
    if not match:
        raise DocumentError(f"{path.name}: no front matter")
    meta = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip().lower()] = value.strip()
    doc_id, title = meta.get("id"), meta.get("title", path.stem)
    level = meta.get("classification", "").lower()
    if not doc_id:
        raise DocumentError(f"{path.name}: front matter has no id")
    if level not in LEVELS:
        raise DocumentError(f"{path.name}: classification must be one of {', '.join(LEVELS)}")

    passages, heading, buffer = [], "Introduction", []

    def flush():
        text = " ".join(" ".join(buffer).split())
        if text:
            n = len(passages) + 1
            passages.append(
                Passage(
                    f"{doc_id}#{n}",
                    doc_id,
                    title,
                    heading,
                    text,
                    level,
                    path.relative_to(root).as_posix(),
                )
            )

    for line in match.group(2).splitlines():
        if line.startswith("## "):
            flush()
            heading, buffer = line[3:].strip(), []
        elif not line.startswith("# "):
            buffer.append(line)
    flush()
    return passages


def load(root: Path, max_classification: str) -> tuple[list[Passage], int]:
    """Passages at or below the ceiling, and how many documents were withheld above it.

    Documents above the ceiling are never parsed into the index, so no retrieval bug, prompt or
    model can surface them: the strongest control is not having the text at all.
    """
    if not root.is_dir():
        raise DocumentError(f"corpus folder not found: {root}")
    ceiling = LEVELS.index(max_classification)
    passages, withheld, seen = [], 0, set()
    for path in sorted(root.rglob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        doc = parse(path, root)
        if not doc:
            continue
        if doc[0].doc_id in seen:
            raise DocumentError(f"{path.name}: duplicate id {doc[0].doc_id}")
        seen.add(doc[0].doc_id)
        if LEVELS.index(doc[0].classification) > ceiling:
            withheld += 1
            continue
        passages.extend(doc)
    return passages, withheld
