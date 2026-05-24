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
    ],
)
def test_deterministic_router(goal, expected):
    assert deterministic_route(goal)["framework_id"] == expected
