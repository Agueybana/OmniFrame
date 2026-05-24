from __future__ import annotations

import json
import os
import re
from typing import TypedDict

import httpx

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
RELATIONSHIP_TERMS = {
    "partner",
    "breakup",
    "girlfriend",
    "boyfriend",
    "wife",
    "husband",
    "relationship",
    "dating",
    "marriage",
    "hollie",
    "family",
    "couple",
}

MODEL_DEFAULTS = {
    "openai": "gpt-5.1",
    "google": "gemini-3.1-pro-preview",
}


def _tokenize(goal: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z][a-zA-Z-]+", goal.lower()))


def deterministic_route(goal: str) -> RouteDecision:
    text = goal.lower()
    tokens = _tokenize(goal)
    if tokens & RELATIONSHIP_TERMS:
        return {
            "framework_id": "swot",
            "confidence": 0.82,
            "rationale": "The goal is a personal relationship decision, so OmniFrame selected SWOT to separate needs, patterns, repair options, and risks without forcing a premature yes/no answer.",
        }

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


def _llm_enabled(provider: str | None = None) -> bool:
    if os.getenv("OMNIFRAME_USE_LLM", "").lower() not in {"1", "true", "yes"}:
        return False
    if provider == "google":
        return bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
    if provider == "openai":
        return bool(os.getenv("OPENAI_API_KEY"))
    return bool(os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))


def _json_from_text(raw: str) -> dict | None:
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        pass

    match = re.search(r"\{.*\}", raw, flags=re.S)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


def _model_choice(provider: str | None, model_id: str | None) -> tuple[str, str]:
    selected_provider = provider if provider in MODEL_DEFAULTS else "openai"
    selected_model = model_id or os.getenv("OMNIFRAME_CANVAS_MODEL") or MODEL_DEFAULTS[selected_provider]
    if selected_provider == "openai" and selected_model.startswith("gemini"):
        selected_provider = "google"
    if selected_provider == "google" and selected_model.startswith("gpt"):
        selected_provider = "openai"
    return selected_provider, selected_model


async def _openai_json(prompt: str, model_id: str) -> dict | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    payload = {
        "model": model_id,
        "input": prompt,
        "tools": [{"type": "web_search_preview"}],
    }
    if model_id.startswith("gpt-5"):
        payload["reasoning"] = {"effort": os.getenv("OMNIFRAME_REASONING_EFFORT", "medium")}

    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    texts: list[str] = []
    for item in data.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                texts.append(content["text"])
    if not texts and data.get("output_text"):
        texts.append(data["output_text"])
    return _json_from_text("\n".join(texts))


async def _google_json(prompt: str, model_id: str) -> dict | None:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent"
    base_payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2},
    }

    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.post(f"{url}?key={api_key}", json={**base_payload, "tools": [{"google_search": {}}]})
        if response.status_code >= 400:
            response = await client.post(f"{url}?key={api_key}", json=base_payload)
        response.raise_for_status()
        data = response.json()

    texts: list[str] = []
    for candidate in data.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            if part.get("text"):
                texts.append(part["text"])
    return _json_from_text("\n".join(texts))


async def _llm_json(prompt: str, provider: str | None, model_id: str | None) -> dict | None:
    selected_provider, selected_model = _model_choice(provider, model_id)
    if not _llm_enabled(selected_provider):
        return None
    try:
        if selected_provider == "google":
            return await _google_json(prompt, selected_model)
        return await _openai_json(prompt, selected_model)
    except Exception:
        return None


async def langchain_route(goal: str, provider: str | None = None, model_id: str | None = None) -> RouteDecision | None:
    if not _llm_enabled(provider):
        return None

    prompt = (
        "Route the user goal to exactly one framework: swot, lean_startup, okrs, porters_five_forces, pestle, rice, or triz.\n"
        "Return compact JSON with framework_id, confidence, and rationale.\n"
        "Use SWOT for broad strategic or personal decision audits, Lean Startup for MVP validation, OKRs for measurable alignment, "
        "Porter's Five Forces for industry structure, PESTLE for macro risk, RICE for prioritization, and TRIZ for engineering contradictions.\n"
        "For relationship, dating, breakup, or family decisions, prefer swot unless the user explicitly requests another framework.\n\n"
        f"Goal: {goal}"
    )

    try:
        parsed = await _llm_json(prompt, provider, model_id)
        if parsed.get("framework_id") in ACTIVE_FRAMEWORK_IDS:
            return {
                "framework_id": parsed["framework_id"],
                "confidence": float(parsed.get("confidence", 0.74)),
                "rationale": str(parsed.get("rationale", "Routed by LangChain LLM policy.")),
            }
    except Exception:
        return None

    return None


async def langchain_enrich_canvas(framework_id: str, goal: str, canvas: dict, provider: str | None = None, model_id: str | None = None) -> dict | None:
    prompt = (
        "You are OmniFrame's senior framework analyst with web research enabled when available. Return only valid JSON.\n"
        "Preserve the current canvas schema and top-level type exactly, but rewrite generic content into concrete, domain-specific analysis.\n"
        "Use the user's exact context, names, constraints, and emotional/business/engineering details. If the prompt is personal or relationship-related, avoid business jargon.\n"
        "For relationship decisions, do not decide for the user; organize values, patterns, boundaries, repair options, safety concerns, and conversation experiments.\n"
        "For every drilldown panel, provide options that directly reference the original user input and the current framework.\n"
        "Use reputable public web context where useful, but do not include citations in the JSON unless a field already supports them.\n\n"
        f"Framework: {framework_id}\n"
        f"Goal: {goal}\n"
        f"Current canvas JSON:\n{json.dumps(canvas)}"
    )
    parsed = await _llm_json(prompt, provider, model_id)
    if isinstance(parsed, dict) and parsed.get("type") == canvas.get("type"):
        return parsed
    return None


async def route_goal(goal: str, framework_id: str | None = None, model_provider: str | None = None, model_id: str | None = None) -> dict:
    if framework_id:
        framework = get_framework(framework_id)
        if not framework or framework_id not in ACTIVE_FRAMEWORK_IDS:
            decision = deterministic_route(goal)
        else:
            canvas = build_canvas(framework_id, goal)
            enriched = await langchain_enrich_canvas(framework_id, goal, canvas, model_provider, model_id)
            return {
                "framework_id": framework_id,
                "framework_name": framework["name"],
                "confidence": 1.0,
                "rationale": f"User selected {framework['name']} after reviewing OmniFrame's recommendation.",
                "canvas": enriched or canvas,
            }
    else:
        decision = await langchain_route(goal, model_provider, model_id) or deterministic_route(goal)
    framework = get_framework(decision["framework_id"])
    if not framework:
        decision = deterministic_route(goal)
        framework = get_framework(decision["framework_id"])

    canvas = build_canvas(decision["framework_id"], goal)
    enriched = await langchain_enrich_canvas(decision["framework_id"], goal, canvas, model_provider, model_id)
    return {
        "framework_id": decision["framework_id"],
        "framework_name": framework["name"],
        "confidence": decision["confidence"],
        "rationale": decision["rationale"],
        "canvas": enriched or canvas,
    }
