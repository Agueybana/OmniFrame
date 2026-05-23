import pytest

from backend.app.services.router import deterministic_route


@pytest.mark.parametrize(
    ("goal", "expected"),
    [
        ("Prioritize our backlog of onboarding features for the next sprint", "rice"),
        ("Design a lighter drone frame without losing strength", "triz"),
        ("Assess whether we should enter the Latin American market", "swot"),
    ],
)
def test_deterministic_router(goal, expected):
    assert deterministic_route(goal)["framework_id"] == expected

