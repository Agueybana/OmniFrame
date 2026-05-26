import pytest

from backend.app.services import router
from backend.app.services.router import deterministic_route, route_goal


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
        ("commercialize an algorithm for optimizing warehouse routing files.", "lean_startup"),
    ],
)
def test_deterministic_router(goal, expected):
    assert deterministic_route(goal)["framework_id"] == expected


def test_deterministic_router_exposes_smart_criteria_process():
    decision = deterministic_route("Rank features for an MVP while validating traction before we build too much")

    assert decision["selection_process"]["passes"][0]["name"] == "Intent criteria"
    assert decision["selection_process"]["passes"][1]["name"] == "Output-fit criteria"
    assert decision["selection_process"]["selected_framework"] in {"rice", "lean_startup"}


def test_router_selection_process_uses_prompt_subject_without_hardcoded_domain():
    decision = deterministic_route("commercialize an algorithm for optimizing warehouse routing files.")
    brief = decision["selection_process"]["domain_brief"]

    assert brief["subject"] == "commercialize an algorithm for optimizing warehouse routing files"
    assert "warehouse" in decision["rationale"]
    assert decision["framework_id"] == "lean_startup"


def test_route_goal_uses_llm_domain_brief_for_canvas(monkeypatch):
    async def fake_llm_json(prompt, provider=None, model_id=None):
        if "Domain Analyst" in prompt:
            return {
                "subject": "commercializing a reef-safe sunscreen formulation",
                "domain": "cosmetic chemistry, reef-safe claims, retail distribution, and consumer skincare",
                "users": "beach travelers, dermatology-aware consumers, coastal retailers, and formulation partners",
                "workflow": "turn a lab formulation into tested SPF claims, compliant packaging, retail proof, and repeat purchase",
                "value_hypothesis": "customers pay if protection, skin feel, reef-safe credibility, and regulatory claims are trustworthy",
                "constraints": "SPF testing, claim substantiation, ingredient restrictions, stability, retail margins, and consumer trust",
                "proof_metrics": ["SPF test pass", "repeat purchase intent", "retailer pilot conversion"],
                "evidence_prompts": ["Run SPF and stability testing before retail pilots.", "Interview coastal retailers about claim credibility.", "Compare with mineral sunscreen substitutes."],
                "adoption_risks": ["Unsubstantiated reef-safe claims can damage trust.", "Texture may lose consumers even if claims are strong.", "Retailers may require margin and compliance proof."],
            }
        return None

    monkeypatch.setenv("OMNIFRAME_USE_LLM", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(router, "_llm_json", fake_llm_json)
    payload = __import__("asyncio").run(route_goal("commercialize a reef-safe sunscreen formula", "swot", "openai", "gpt-5.1"))
    rendered = str(payload)

    assert payload["selection_process"]["domain_brief"]["subject"] == "commercializing a reef-safe sunscreen formulation"
    assert "reef-safe" in rendered
    assert "SPF" in rendered


def test_generate_component_result_feeds_prompt_and_details_to_llm(monkeypatch):
    captured = {}

    async def fake_llm_json(prompt, provider=None, model_id=None, **kwargs):
        captured["prompt"] = prompt
        return {"text": "GENERATED COMPONENT BODY"}

    monkeypatch.setattr(router, "_llm_json", fake_llm_json)
    component = {
        "id": "strengths",
        "label": "Strengths",
        "prompt": "DISTINCTIVE_COMPONENT_PROMPT_INSTRUCTION",
        "description": "short description",
    }
    result = __import__("asyncio").run(
        router.generate_component_result("swot", component, "PROJECT_DETAIL_CONTEXT", "goal text")
    )

    assert result == "GENERATED COMPONENT BODY"  # response becomes the component field
    assert "DISTINCTIVE_COMPONENT_PROMPT_INSTRUCTION" in captured["prompt"]  # prompt drives the LLM
    assert "PROJECT_DETAIL_CONTEXT" in captured["prompt"]
