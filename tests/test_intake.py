import json
from pathlib import Path

import pytest

from aief import intake
from aief.cli import main

EXAMPLES = Path(__file__).parent.parent / "examples" / "intake"


def base(**changes) -> dict:
    data = {
        "id": "UC-1",
        "title": "Test",
        "task": "answer_from_documents",
        "users": 40,
        "uses_per_month": 600,
        "minutes_saved_per_use": 10,
        "tokens_per_use": 4000,
        "data": {"classification": "internal", "personal_data": False, "source_quality": "curated"},
        "actions": "draft",
        "error_tolerance": "medium",
        "systems": ["library"],
        "owner_after_launch": "Desk",
    }
    data.update(changes)
    return data


def scores(a: intake.Assessment) -> dict:
    return {s.criterion: s.score for s in a.scores}


def test_good_case_proceeds_with_the_rag_pattern():
    a = intake.assess(base())
    assert a.decision == "Proceed to proof of concept"
    assert a.pattern.id == "P1"
    assert a.topology == "hybrid"
    assert a.hours_saved_per_month == 100.0


@pytest.mark.parametrize(
    "classification,personal,topology",
    [
        ("public", False, "any"),
        ("internal", False, "hybrid"),
        ("internal", True, "hybrid"),
        ("restricted", False, "local"),
        ("confidential", True, "local"),
    ],
)
def test_topology_follows_the_data(classification, personal, topology):
    a = intake.assess(base(data={"classification": classification, "personal_data": personal}))
    assert a.topology == topology
    if topology == "local":
        assert any("local_only" in c for c in a.controls)


def test_external_actions_on_restricted_data_score_lowest_security():
    a = intake.assess(
        base(
            task="multi_step_with_actions",
            actions="external",
            data={"classification": "restricted"},
        )
    )
    assert scores(a)["security"] == 1
    assert a.decision == "Proceed only with conditions"
    assert any("four eyes" in c for c in a.controls)
    assert any("Policy engine" in c for c in a.controls)


def test_no_owner_parks_the_case():
    a = intake.assess(base(owner_after_launch=None))
    assert a.decision.startswith("Park")
    assert scores(a)["operational sustainability"] == 1


def test_local_topology_has_no_per_use_api_cost_score():
    small = intake.assess(base(data={"classification": "restricted"}, uses_per_month=100))
    large = intake.assess(base(data={"classification": "restricted"}, uses_per_month=50_000))
    assert scores(small)["cost"] == 4
    assert scores(large)["cost"] == 3  # needs a GPU server


def test_commercial_cost_estimate_uses_the_price_given():
    a = intake.assess(base(uses_per_month=1000, tokens_per_use=1000, price_per_mtok=10))
    assert a.monthly_tokens == 1_000_000
    assert a.commercial_cost_usd == 10.0


def test_low_value_is_flagged():
    a = intake.assess(base(uses_per_month=10, minutes_saved_per_use=5))
    assert any("below the 20-hour bar" in c for c in a.conditions)


@pytest.mark.parametrize(
    "change,message",
    [
        ({"task": "write_poems"}, "task must be one of"),
        ({"actions": "delete"}, "actions must be one of"),
        ({"users": "many"}, "users must be a number"),
        ({"data": {}}, "missing field: classification"),
    ],
)
def test_invalid_input_is_explained(change, message):
    with pytest.raises(intake.IntakeError, match=message):
        intake.assess(base(**change))


def test_examples_match_their_committed_assessments():
    for path in sorted(EXAMPLES.glob("*.yaml")):
        expected = path.with_suffix(".assessment.md").read_text(encoding="utf-8")
        assert intake.to_markdown(intake.assess(intake.load(path))) == expected, path.name


def test_cli_json_and_error(tmp_path, capsys):
    assert main(["intake", "--format", "json", str(EXAMPLES / "staff-case-routing.yaml")]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["topology"] == "local"
    bad = tmp_path / "bad.yaml"
    bad.write_text("- a list\n", encoding="utf-8")
    assert main(["intake", str(bad)]) == 2
