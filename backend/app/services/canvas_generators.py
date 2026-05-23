from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


def _topic(goal: str) -> str:
    cleaned = re.sub(r"\s+", " ", goal.strip())
    return cleaned[:140].rstrip(".")


def generate_swot(goal: str) -> dict[str, Any]:
    topic = _topic(goal)
    return {
        "type": "quadrant",
        "title": "SWOT Strategy Canvas",
        "subtitle": f"Baseline audit for: {topic}",
        "sections": [
            {
                "id": "strengths",
                "label": "Strengths",
                "prompt": "Internal advantages to preserve or amplify.",
                "items": [
                    f"Existing capability that could accelerate {topic.lower()}",
                    "Differentiated data, expertise, relationships, or brand trust",
                    "Operational asset that competitors would struggle to copy",
                ],
            },
            {
                "id": "weaknesses",
                "label": "Weaknesses",
                "prompt": "Internal limitations that could slow execution.",
                "items": [
                    "Skill, budget, data, or process gap that creates delivery risk",
                    "Assumption that needs validation before scaling",
                    "Dependency that could become a bottleneck",
                ],
            },
            {
                "id": "opportunities",
                "label": "Opportunities",
                "prompt": "External openings worth exploiting.",
                "items": [
                    "Market shift, customer pain, or regulatory change creating urgency",
                    "Partnership or distribution channel that could compound reach",
                    "Underserved segment where speed matters more than perfection",
                ],
            },
            {
                "id": "threats",
                "label": "Threats",
                "prompt": "External forces that could reduce odds of success.",
                "items": [
                    "Competitive response, substitute, or switching-cost issue",
                    "Technical, legal, or adoption risk outside direct control",
                    "Timing risk if the market window closes before launch",
                ],
            },
        ],
    }


def generate_rice(goal: str) -> dict[str, Any]:
    topic = _topic(goal)
    rows = [
        {
            "initiative": "Validate highest-risk assumption",
            "reach": 800,
            "impact": 3,
            "confidence": 80,
            "effort": 2,
        },
        {
            "initiative": "Ship narrow prototype for the strongest user segment",
            "reach": 500,
            "impact": 4,
            "confidence": 70,
            "effort": 4,
        },
        {
            "initiative": "Instrument decision and adoption metrics",
            "reach": 1000,
            "impact": 2,
            "confidence": 90,
            "effort": 2,
        },
    ]
    for row in rows:
        row["score"] = round(row["reach"] * row["impact"] * (row["confidence"] / 100) / row["effort"], 1)

    return {
        "type": "score_table",
        "title": "RICE Prioritization Canvas",
        "subtitle": f"Cold ranking model for: {topic}",
        "formula": "Reach x Impact x Confidence / Effort",
        "rows": rows,
    }


@dataclass(frozen=True)
class TrizPrinciple:
    number: int
    name: str
    application: str


TRIZ_STARTERS = [
    TrizPrinciple(1, "Segmentation", "Break the system into independent modules so each constraint can be optimized separately."),
    TrizPrinciple(10, "Preliminary action", "Move expensive or slow preparation before the critical moment."),
    TrizPrinciple(15, "Dynamics", "Let structure, policy, or configuration adapt as conditions change."),
    TrizPrinciple(24, "Intermediary", "Introduce a buffer, broker, adapter, or translation layer between conflicting needs."),
    TrizPrinciple(35, "Parameter change", "Change density, timing, temperature, precision, or another key parameter instead of forcing the same design."),
]


def generate_triz(goal: str) -> dict[str, Any]:
    topic = _topic(goal)
    return {
        "type": "contradiction",
        "title": "TRIZ Contradiction Canvas",
        "subtitle": f"Inventive problem-solving for: {topic}",
        "contradiction": {
            "improving": "The desired improvement the user wants to maximize",
            "worsening": "The system property that appears to get worse when improving it",
            "prompt": "Rewrite these two fields into a crisp contradiction before selecting a principle.",
        },
        "principles": [principle.__dict__ for principle in TRIZ_STARTERS],
        "solution_cards": [
            {
                "title": "Separate in time",
                "body": "Make the system behave one way during exploration and another way during execution.",
            },
            {
                "title": "Separate in structure",
                "body": "Split the fragile or expensive part away from the part that must move quickly.",
            },
            {
                "title": "Introduce a mediation layer",
                "body": "Use an adapter, queue, policy engine, or human review gate to absorb the conflict.",
            },
        ],
    }


GENERATORS = {
    "swot": generate_swot,
    "rice": generate_rice,
    "triz": generate_triz,
}


def build_canvas(framework_id: str, goal: str) -> dict[str, Any]:
    return GENERATORS[framework_id](goal)

