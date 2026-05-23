from __future__ import annotations

import json
import os
import re
from typing import TypedDict

from .canvas_generators import build_canvas
from .frameworks import get_framework


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


def _tokenize(goal: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z][a-zA-Z-]+", goal.lower()))


def deterministic_route(goal: str) -> RouteDecision:
    text = goal.lower()
    tokens = _tokenize(goal)
    scores = {
        "swot": len(tokens & SWOT_TERMS) + sum(phrase in text for phrase in ["new market", "go to market", "business strategy"]),
        "rice": len(tokens & RICE_TERMS) + sum(phrase in text for phrase in ["what to build", "which feature", "next sprint"]),
        "triz": len(tokens & TRIZ_TERMS) + sum(phrase in text for phrase in ["but it", "trade off", "tradeoff", "without increasing"]),
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
                "You route goals to exactly one framework: swot, rice, or triz. "
                "Return compact JSON with framework_id, confidence, and rationale. "
                "Use SWOT for strategic baseline audits, RICE for prioritization, and TRIZ for engineering contradictions.",
            ),
            ("human", "{goal}"),
        ]
    )
    model = ChatOpenAI(model=os.getenv("OMNIFRAME_ROUTER_MODEL", "gpt-4.1-mini"), temperature=0)
    chain = prompt | model | StrOutputParser()

    try:
        raw = await chain.ainvoke({"goal": goal})
        parsed = json.loads(raw)
        if parsed.get("framework_id") in {"swot", "rice", "triz"}:
            return {
                "framework_id": parsed["framework_id"],
                "confidence": float(parsed.get("confidence", 0.74)),
                "rationale": str(parsed.get("rationale", "Routed by LangChain LLM policy.")),
            }
    except Exception:
        return None

    return None


async def route_goal(goal: str) -> dict:
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

