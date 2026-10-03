"""Use-case intake: score a proposed AI use case and recommend a pattern, a topology and controls.

The scoring is deterministic and every score carries its reason, so a requester can see why a
case was parked and what would change the outcome. It is a triage aid for the first
conversation with a business owner, not a decision: the decision record is signed by a person.

The seven criteria are the ones an enterprise AI lab is asked to assess: feasibility,
information sensitivity, security, cost, scalability, interoperability and operational
sustainability. Value (time saved) is reported next to them, not blended in, so a valuable but
risky case is visible as exactly that.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml

CLASSIFICATIONS = ["public", "internal", "restricted", "confidential"]
ACTIONS = ["read", "draft", "external"]
SOURCE_QUALITY = ["curated", "mixed", "unmanaged"]
TOLERANCE = ["low", "medium", "high"]

# Illustrative blended price for a commercial model, in USD per million tokens. It is a
# placeholder for the order of magnitude: set `price_per_mtok` in the intake file from the
# current price list of the model you would actually use.
DEFAULT_PRICE_PER_MTOK = 3.0
# Above this many model calls a month, a local deployment needs a GPU server rather than a
# shared CPU host (a planning threshold, to be replaced by your own load test).
LOCAL_GPU_THRESHOLD = 5_000


@dataclass(frozen=True)
class Pattern:
    id: str
    name: str
    reference: str  # reference implementation repository


PATTERNS = {
    "answer_from_documents": Pattern(
        "P1", "Governed retrieval (RAG) with a sensitivity ceiling", "policy-evidence-mcp"
    ),
    "assistant_tool_access": Pattern("P2", "Read-only MCP tool server", "policy-evidence-mcp"),
    "data_to_text": Pattern("P3", "Code computes, model writes, code checks", "oecd-data-pipeline"),
    "match_or_classify": Pattern(
        "P4",
        "Deterministic first, model chooses among retrieved candidates, people review the rest",
        "reference-resolver-agent",
    ),
    "multi_step_with_actions": Pattern(
        "P5", "Governed agent with policy engine and human approval", "governed-agents"
    ),
    "team_knowledge_in_assistant": Pattern(
        "P6", "Curated knowledge layer for an enterprise assistant", "copilot-team-knowledge"
    ),
}
PLATFORM = [
    "C1 Model gateway: routing, budgets, personal-data masking (governed-llm-gateway)",
    "C2 Reference deployment: hardened containers, monitoring, runbook (governed-ai-platform)",
]


class IntakeError(ValueError):
    """The intake file is incomplete or uses a value outside the allowed list."""


@dataclass
class Score:
    criterion: str
    score: int  # 1 (unfavourable) to 5 (favourable)
    reason: str


@dataclass
class Assessment:
    id: str
    title: str
    owner: str | None
    pattern: Pattern
    topology: str
    topology_reason: str
    scores: list[Score]
    average: float
    hours_saved_per_month: float
    monthly_tokens: int
    commercial_cost_usd: float
    price_per_mtok: float
    controls: list[str]
    decision: str
    conditions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["pattern"] = asdict(self.pattern)
        return data


def _choice(data: dict, key: str, allowed: list[str], default: str | None = None) -> str:
    value = data.get(key, default)
    if value is None:
        raise IntakeError(f"missing field: {key}")
    value = str(value).strip().lower()
    if value not in allowed:
        raise IntakeError(f"{key} must be one of {', '.join(allowed)} (got {value!r})")
    return value


def _number(data: dict, key: str, default: float | None = None) -> float:
    value = data.get(key, default)
    if value is None:
        raise IntakeError(f"missing field: {key}")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise IntakeError(f"{key} must be a number (got {value!r})") from exc
    if number < 0:
        raise IntakeError(f"{key} must not be negative")
    return number


def _clamp(n: int) -> int:
    return max(1, min(5, n))


def load(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    data = json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text)
    if not isinstance(data, dict):
        raise IntakeError("the intake file must contain a mapping of fields")
    return data


def assess(data: dict) -> Assessment:
    task = str(data.get("task", "")).strip().lower()
    if task not in PATTERNS:
        raise IntakeError(f"task must be one of {', '.join(PATTERNS)} (got {task!r})")
    pattern = PATTERNS[task]
    d = data.get("data") or {}
    classification = _choice(d, "classification", CLASSIFICATIONS)
    personal = bool(d.get("personal_data", False))
    quality = _choice(d, "source_quality", SOURCE_QUALITY, "mixed")
    actions = _choice(data, "actions", ACTIONS)
    tolerance = _choice(data, "error_tolerance", TOLERANCE, "medium")
    users = int(_number(data, "users"))
    uses = int(_number(data, "uses_per_month"))
    minutes = _number(data, "minutes_saved_per_use")
    tokens = int(_number(data, "tokens_per_use", 3000))
    price = _number(data, "price_per_mtok", DEFAULT_PRICE_PER_MTOK)
    systems = list(data.get("systems") or [])
    apis = bool(data.get("systems_have_apis", True))
    reusable = bool(data.get("reusable_across_units", False))
    owner_after = data.get("owner_after_launch")

    # Topology follows the data, not the model preference.
    if classification in {"restricted", "confidential"}:
        topology = "local"
        topology_reason = (
            f"{classification} information: open-weight models on the organisation's own "
            "infrastructure only (gateway policy local_only)"
        )
    elif classification == "internal" and personal:
        topology = "hybrid"
        topology_reason = (
            "internal information with personal data: commercial models in the organisation's "
            "tenant, requests with personal data kept on a local model (local_if_pii)"
        )
    elif classification == "internal":
        topology = "hybrid"
        topology_reason = (
            "internal information: commercial models in the organisation's tenant or local "
            "models, chosen per task by the gateway; personal data masked before it leaves"
        )
    else:
        topology = "any"
        topology_reason = "public information: the cheapest adequate model, local or commercial"

    scores: list[Score] = []

    # Feasibility: a known pattern, the state of the sources, and how costly a wrong answer is.
    f, why = 5, [f"known pattern {pattern.id}"]
    if quality == "mixed":
        f -= 1
        why.append("sources are mixed (drafts next to finals)")
    elif quality == "unmanaged":
        f -= 2
        why.append("sources are unmanaged: curation comes first")
    if tolerance == "low" and task in {"multi_step_with_actions", "answer_from_documents"}:
        f -= 1
        why.append("low tolerance for error needs validated citations and review")
    scores.append(Score("feasibility", _clamp(f), "; ".join(why)))

    # Information sensitivity.
    s = {"public": 5, "internal": 4, "restricted": 2, "confidential": 1}[classification]
    why = [f"{classification} information"]
    if personal:
        s -= 1
        why.append("personal data")
    scores.append(Score("information sensitivity", _clamp(s), "; ".join(why)))

    # Security: what the system can do, given what it can see.
    sec = {"read": 5, "draft": 4, "external": 2}[actions]
    why = [f"most consequential action: {actions}"]
    if actions == "external" and classification in {"restricted", "confidential"}:
        sec = 1
        why.append("external actions on restricted information")
    scores.append(Score("security", _clamp(sec), "; ".join(why)))

    # Cost: per-use API spend for cloud and hybrid; fixed infrastructure for local.
    monthly_tokens = uses * tokens
    commercial_cost = round(monthly_tokens / 1_000_000 * price, 2)
    if topology == "local":
        c = 3 if uses > LOCAL_GPU_THRESHOLD else 4
        reason = "no per-use API cost; " + (
            "volume needs a GPU server" if c == 3 else "volume fits a shared CPU or small GPU"
        )
    else:
        thresholds = [(50, 5), (250, 4), (1_000, 3), (5_000, 2)]
        c = next((score for limit, score in thresholds if commercial_cost < limit), 1)
        reason = f"about {commercial_cost:,.2f} USD a month at {price} USD per million tokens"
    scores.append(Score("cost", c, reason))

    # Scalability: one team, or a pattern several units can reuse.
    sc, why = 3, []
    if reusable:
        sc += 1
        why.append("reusable across units")
    if users >= 50:
        sc += 1
        why.append(f"{users} users")
    if users < 5:
        sc -= 1
        why.append(f"only {users} users")
    scores.append(Score("scalability", _clamp(sc), "; ".join(why) or f"{users} users, one unit"))

    # Interoperability: the systems it must connect to.
    if not systems:
        i, reason = 5, "no system integration"
    elif not apis:
        i, reason = 2, f"{len(systems)} systems without usable APIs"
    else:
        i = 5 if len(systems) <= 2 else 4
        reason = f"{len(systems)} systems with APIs: {', '.join(map(str, systems))}"
    scores.append(Score("interoperability", i, reason))

    # Operational sustainability: someone owns it after launch.
    if owner_after:
        o = 5 if tolerance == "high" else 4
        reason = f"owned after launch by {owner_after}"
    else:
        o, reason = 1, "no owner after launch"
    scores.append(Score("operational sustainability", o, reason))

    average = round(sum(x.score for x in scores) / len(scores), 2)
    hours = round(uses * minutes / 60, 1)

    controls = [
        "Evaluation set agreed with the business owner before the pilot, run in CI",
        "Model calls through the gateway: team budget, audit ledger without content",
    ]
    if task in {"answer_from_documents", "assistant_tool_access", "team_knowledge_in_assistant"}:
        controls.append(
            f"Sensitivity ceiling enforced in retrieval: nothing above {classification}"
        )
    if personal and topology != "local":
        controls.append("Personal data masked at the gateway, or the team set to local_if_pii")
    if topology == "local":
        controls.append("Gateway policy local_only: no route to an external provider exists")
    if actions == "draft":
        controls.append("Outputs labelled as drafts; a person sends or files them")
    if actions == "external":
        controls.append("Every external action approved by a named person (four eyes)")
        controls.append("Egress allow-list for recipients and endpoints")
    if tolerance == "low":
        controls.append("Citations or figures validated in code; failures go to a review queue")
    if task in {"multi_step_with_actions"}:
        controls.append("Policy engine on every tool call, step and cost budgets, kill switch")

    conditions = [f"{x.criterion}: {x.reason}" for x in scores if x.score <= 2]
    if not owner_after:
        decision = "Park: no owner after launch"
    elif any(x.score == 1 for x in scores):
        decision = "Proceed only with conditions"
    elif average >= 3.5 and hours >= 20:
        decision = "Proceed to proof of concept"
    elif average >= 2.5:
        decision = "Proceed with conditions"
    else:
        decision = "Park"
    if hours < 20:
        conditions.append(f"value: about {hours} hours saved a month, below the 20-hour bar")

    return Assessment(
        id=str(data.get("id", "UC-?")),
        title=str(data.get("title", "Untitled use case")),
        owner=data.get("owner"),
        pattern=pattern,
        topology=topology,
        topology_reason=topology_reason,
        scores=scores,
        average=average,
        hours_saved_per_month=hours,
        monthly_tokens=monthly_tokens,
        commercial_cost_usd=commercial_cost,
        price_per_mtok=price,
        controls=controls,
        decision=decision,
        conditions=conditions,
    )


def to_markdown(a: Assessment) -> str:
    lines = [
        f"# {a.id}: {a.title}",
        "",
        f"**Decision (proposed): {a.decision}**  ",
        f"Pattern: {a.pattern.id} {a.pattern.name} (reference: `{a.pattern.reference}`)  ",
        f"Topology: **{a.topology}**: {a.topology_reason}  ",
        f"Value: about {a.hours_saved_per_month:,.1f} hours saved a month",
        "",
        "| Criterion | Score (1-5) | Reason |",
        "|---|---|---|",
    ]
    lines += [f"| {s.criterion} | {s.score} | {s.reason} |" for s in a.scores]
    lines += [f"| **average** | **{a.average}** | |", ""]
    lines.append(
        f"Model usage: about {a.monthly_tokens:,} tokens a month; at an illustrative "
        f"{a.price_per_mtok} USD per million tokens a commercial model would cost about "
        f"{a.commercial_cost_usd:,.2f} USD a month."
    )
    lines += ["", "## Controls", ""] + [f"- {c}" for c in a.controls]
    lines += ["", "## Platform components", ""] + [f"- {c}" for c in PLATFORM]
    if a.conditions:
        lines += ["", "## Conditions to resolve", ""] + [f"- {c}" for c in a.conditions]
    lines += [
        "",
        "_A triage aid, not a decision: the decision record is signed by the business owner and "
        "the AI lab._",
    ]
    return "\n".join(lines) + "\n"
