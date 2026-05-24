from __future__ import annotations

import json
import os
import re
from typing import TypedDict

from .canvas_generators import build_canvas
from .frameworks import ACTIVE_FRAMEWORK_IDS, get_framework


class RouteDecision(TypedDict):
    framework_id: str
    confidence: float
    rationale: str


SWOT_TERMS = {
    "strategy",
    "market",
    "competitor",
    "competitive",
    "launch",
    "expansion",
    "audit",
    "positioning",
    "opportunity",
    "threat",
}
RICE_TERMS = {
    "prioritize",
    "priority",
    "roadmap",
    "backlog",
    "feature",
    "features",
    "rank",
    "score",
    "effort",
    "impact",
    "product",
}
TRIZ_TERMS = {
    "contradiction",
    "engineering",
    "constraint",
    "constraints",
    "paradox",
    "optimize",
    "stronger",
    "lighter",
    "faster",
    "cheaper",
    "invent",
    "design problem",
}
LEAN_TERMS = {
    "mvp",
    "experiment",
    "validate",
    "validation",
    "hypothesis",
    "lean",
    "pivot",
    "traction",
    "startup",
    "prototype",
}
OKR_TERMS = {
    "okr",
    "objective",
    "objectives",
    "key result",
    "key results",
    "alignment",
    "quarter",
    "quarterly",
    "goal",
    "goals",
    "measure",
}
PORTER_TERMS = {
    "industry",
    "rivalry",
    "entrant",
    "entrants",
    "substitute",
    "supplier",
    "buyer",
    "profitability",
    "competition",
    "competitive",
}
PESTLE_TERMS = {
    "regulation",
    "regulatory",
    "legal",
    "political",
    "economic",
    "social",
    "environmental",
    "global",
    "macro",
    "compliance",
    "policy",
}


def _tokenize(goal: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z][a-zA-Z-]+", goal.lower()))


def deterministic_route(goal: str) -> RouteDecision:
    text = goal.lower()
    tokens = _tokenize(goal)
    scores = {
        "swot": len(tokens & SWOT_TERMS) + sum(phrase in text for phrase in ["new market", "go to market", "business strategy"]),
        "rice": len(tokens & RICE_TERMS) + sum(phrase in text for phrase in ["what to build", "which feature", "next sprint"]),
        "triz": len(tokens & TRIZ_TERMS) + sum(phrase in text for phrase in ["but it", "trade off", "tradeoff", "without increasing"]),
        "lean_startup": len(tokens & LEAN_TERMS) + sum(phrase in text for phrase in ["product market fit", "test demand", "landing page"]),
        "okrs": len(tokens & OKR_TERMS) + sum(phrase in text for phrase in ["align teams", "quarterly targets", "company goals"]),
        "porters_five_forces": len(tokens & PORTER_TERMS) + sum(phrase in text for phrase in ["five forces", "market attractiveness", "industry structure"]),
        "pestle": len(tokens & PESTLE_TERMS) + sum(phrase in text for phrase in ["global expansion", "macro environment", "regulatory risk"]),
    }

    winner = max(scores, key=scores.get)
    top_score = scores[winner]
    total_signal = sum(scores.values())

    if total_signal == 0:
        winner = "swot"
        confidence = 0.58
        rationale = "No strong specialist signal was detected, so OmniFrame selected SWOT as the safest broad diagnostic route."
    else:
        confidence = min(0.92, 0.62 + (top_score / max(total_signal, 1)) * 0.3)
        rationale = {
            "swot": "The goal reads like a strategic baseline assessment with internal and external factors.",
            "rice": "The goal is asking for prioritization, ranking, or roadmap tradeoffs.",
            "triz": "The goal contains an engineering contradiction or constraint conflict that needs inventive resolution.",
            "lean_startup": "The goal is asking for fast validation, MVP design, or evidence before committing capital.",
            "okrs": "The goal needs measurable alignment between objectives, key results, and execution work.",
            "porters_five_forces": "The goal is about industry attractiveness, competitive pressure, and structural profitability.",
            "pestle": "The goal depends on macro-environmental forces such as regulation, economics, technology, or legal risk.",
        }[winner]

    return {"framework_id": winner, "confidence": round(confidence, 2), "rationale": rationale}


def _langchain_enabled() -> bool:
    return os.getenv("OMNIFRAME_USE_LLM", "").lower() in {"1", "true", "yes"} and bool(os.getenv("OPENAI_API_KEY"))


async def langchain_route(goal: str) -> RouteDecision | None:
    if not _langchain_enabled():
        return None

    try:
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import ChatOpenAI
    except Exception:
        return None

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You route goals to exactly one framework: swot, lean_startup, okrs, porters_five_forces, pestle, rice, or triz. "
                "Return compact JSON with framework_id, confidence, and rationale. "
                "Use SWOT for broad strategic audits, Lean Startup for MVP validation, OKRs for measurable alignment, "
                "Porter's Five Forces for industry structure, PESTLE for macro risk, RICE for prioritization, and TRIZ for engineering contradictions.",
            ),
            ("human", "{goal}"),
        ]
    )
    model = ChatOpenAI(model=os.getenv("OMNIFRAME_ROUTER_MODEL", "gpt-4.1-mini"), temperature=0)
    chain = prompt | model | StrOutputParser()

    try:
        raw = await chain.ainvoke({"goal": goal})
        parsed = json.loads(raw)
        if parsed.get("framework_id") in ACTIVE_FRAMEWORK_IDS:
            return {
                "framework_id": parsed["framework_id"],
                "confidence": float(parsed.get("confidence", 0.74)),
                "rationale": str(parsed.get("rationale", "Routed by LangChain LLM policy.")),
            }
    except Exception:
        return None

    return None


async def route_goal(goal: str, framework_id: str | None = None) -> dict:
    if framework_id:
        framework = get_framework(framework_id)
        if not framework or framework_id not in ACTIVE_FRAMEWORK_IDS:
            decision = deterministic_route(goal)
        else:
            return {
                "framework_id": framework_id,
                "framework_name": framework["name"],
                "confidence": 1.0,
                "rationale": f"User selected {framework['name']} after reviewing OmniFrame's recommendation.",
                "canvas": build_canvas(framework_id, goal),
            }
    else:
        decision = await langchain_route(goal) or deterministic_route(goal)
    framework = get_framework(decision["framework_id"])
    if not framework:
        decision = deterministic_route(goal)
        framework = get_framework(decision["framework_id"])

    return {
        "framework_id": decision["framework_id"],
        "framework_name": framework["name"],
        "confidence": decision["confidence"],
        "rationale": decision["rationale"],
        "canvas": build_canvas(decision["framework_id"], goal),
    }
