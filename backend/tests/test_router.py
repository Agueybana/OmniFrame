import pytest

from backend.app.services.router import deterministic_route


@pytest.mark.parametrize(
    ("goal", "expected"),
    [
        ("Prioritize our backlog of onboarding features for the next sprint", "rice"),
        ("Design a lighter drone frame without losing strength", "triz"),
        ("Assess whether we should enter the Latin American market", "swot"),
        ("Validate an MVP landing page before we spend engineering budget", "lean_startup"),
        ("Set quarterly objectives and key results for the product team", "okrs"),
        ("Analyze supplier power and substitute threats in this industry", "porters_five_forces"),
        ("Assess legal regulatory and economic risks before global expansion", "pestle"),
        ("Help me decide whether leaving my partner Hollie is the best choice", "swot"),
        ("Find a girlfriend", "swot"),
        ("commercialize an algorithm for optimizing a CNC file.", "lean_startup"),
    ],
)
def test_deterministic_router(goal, expected):
    assert deterministic_route(goal)["framework_id"] == expected


def test_deterministic_router_exposes_smart_criteria_process():
    decision = deterministic_route("Rank features for an MVP while validating traction before we build too much")

    assert decision["selection_process"]["passes"][0]["name"] == "Intent criteria"
    assert decision["selection_process"]["passes"][1]["name"] == "Output-fit criteria"
    assert decision["selection_process"]["selected_framework"] in {"rice", "lean_startup"}


def test_router_selection_process_is_prompt_specific_for_cnc():
    decision = deterministic_route("commercialize an algorithm for optimizing a CNC file.")
    brief = decision["selection_process"]["domain_brief"]

    assert "CNC" in brief["subject"]
    assert "CAM" in brief["domain"]
    assert "cycle-time" in " ".join(brief["proof_metrics"]) or "cycle time" in " ".join(brief["proof_metrics"])
    assert "CNC/CAM" in decision["rationale"]
