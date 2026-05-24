from __future__ import annotations

import json
import os
import re
from typing import TypedDict

import httpx

from .canvas_generators import build_canvas, extract_domain_brief
from .frameworks import ACTIVE_FRAMEWORK_IDS, get_framework


class RouteDecision(TypedDict):
    framework_id: str
    confidence: float
    rationale: str
    selection_process: dict


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
    "commercialize",
    "commercialization",
    "monetize",
    "buyer",
    "customer",
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
    "commercialize",
    "commercialization",
    "pilot",
    "buyer",
    "customer discovery",
    "proof",
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

FRAMEWORK_NAMES = {
    "swot": "SWOT",
    "lean_startup": "Lean Startup",
    "okrs": "OKRs",
    "porters_five_forces": "Porter's Five Forces",
    "pestle": "PESTLE",
    "rice": "RICE",
    "triz": "TRIZ",
}


def _tokenize(goal: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z][a-zA-Z-]+", goal.lower()))


def _score_pass(goal: str, mode: str) -> dict:
    text = goal.lower()
    tokens = _tokenize(goal)
    brief = extract_domain_brief(goal)
    scores = {framework_id: 0 for framework_id in ACTIVE_FRAMEWORK_IDS}
    signals: dict[str, list[str]] = {framework_id: [] for framework_id in ACTIVE_FRAMEWORK_IDS}

    def add(framework_id: str, points: int, reason: str) -> None:
        scores[framework_id] += points
        if reason and reason not in signals[framework_id]:
            signals[framework_id].append(reason)

    if mode == "intent":
        term_groups = {
            "swot": (SWOT_TERMS, ["new market", "go to market", "business strategy", "personal decision", "should i", "commercialize an algorithm"]),
            "rice": (RICE_TERMS, ["what to build", "which feature", "next sprint", "rank features"]),
            "triz": (TRIZ_TERMS, ["but it", "trade off", "tradeoff", "without increasing", "lighter but"]),
            "lean_startup": (LEAN_TERMS, ["product market fit", "test demand", "landing page", "validate mvp", "commercialize an algorithm", "pilot buyer", "proof of value"]),
            "okrs": (OKR_TERMS, ["align teams", "quarterly targets", "company goals"]),
            "porters_five_forces": (PORTER_TERMS, ["five forces", "market attractiveness", "industry structure"]),
            "pestle": (PESTLE_TERMS, ["global expansion", "macro environment", "regulatory risk"]),
        }
        for framework_id, (terms, phrases) in term_groups.items():
            term_hits = sorted(tokens & terms)
            phrase_hits = [phrase for phrase in phrases if phrase in text]
            if term_hits:
                add(framework_id, len(term_hits), f"keyword signal: {', '.join(term_hits[:4])}")
            for phrase in phrase_hits:
                add(framework_id, 2, f"phrase signal: {phrase}")
        if tokens & RELATIONSHIP_TERMS:
            add("swot", 5, "relationship or personal decision language")
        if "cnc" in tokens or "g-code" in text or "toolpath" in tokens or "machining" in tokens:
            add("lean_startup", 2, "CNC/CAM algorithm commercialization needs buyer proof")
            add("swot", 2, "CNC/CAM market, trust, and integration audit")
    else:
        if any(word in tokens for word in ["rank", "prioritize", "priority", "backlog", "features", "score"]):
            add("rice", 5, "requested output is ranking or prioritization")
        if any(phrase in text for phrase in ["feature list", "rank features", "what should we build", "roadmap"]):
            add("rice", 4, "requested artifact is a scored build list")
        if any(word in tokens for word in ["validate", "mvp", "prototype", "experiment", "traction", "hypothesis"]):
            add("lean_startup", 5, "requested output is validation or experiment design")
        if any(word in tokens for word in ["commercialize", "commercialization", "monetize", "pilot", "buyer"]):
            add("lean_startup", 5, "requested output is commercialization validation")
            add("swot", 3, "commercialization also needs strategic audit")
        if any(word in tokens for word in ["objective", "objectives", "okr", "goals", "quarterly", "alignment"]):
            add("okrs", 5, "requested output is measurable alignment")
        if any(word in tokens for word in ["industry", "supplier", "buyer", "substitute", "entrant", "rivalry", "competition"]):
            add("porters_five_forces", 5, "requested output is industry pressure analysis")
        if any(word in tokens for word in ["legal", "regulatory", "regulation", "policy", "global", "economic", "environmental"]):
            add("pestle", 5, "requested output is macro-environment scan")
        if any(word in tokens for word in ["lighter", "stronger", "cheaper", "faster", "constraint", "contradiction", "material", "engineering"]):
            add("triz", 5, "requested output involves a technical contradiction or design tradeoff")
        if any(word in tokens for word in RELATIONSHIP_TERMS) or any(phrase in text for phrase in ["should i", "decide whether", "best choice"]):
            add("swot", 5, "requested output is a decision audit under uncertainty")
        if not any(scores.values()):
            add("swot", 1, "broad diagnostic fallback")

    winner = max(scores, key=scores.get)
    top_score = scores[winner]
    sorted_scores = sorted(scores.values(), reverse=True)
    margin = top_score - (sorted_scores[1] if len(sorted_scores) > 1 else 0)
    confidence = min(0.94, 0.55 + (top_score * 0.05) + (margin * 0.04))
    return {
        "name": "Intent criteria" if mode == "intent" else "Output-fit criteria",
        "winner": winner,
        "winner_name": FRAMEWORK_NAMES.get(winner, winner),
        "scores": scores,
        "confidence": round(confidence, 2),
        "signals": signals[winner][:4] or [f"broad fit signal for {brief.subject}"],
    }


def _adjudicate_smart_passes(goal: str, intent_pass: dict, output_pass: dict) -> dict:
    text = goal.lower()
    tokens = _tokenize(goal)
    brief = extract_domain_brief(goal)
    scores = {framework_id: intent_pass["scores"].get(framework_id, 0) + output_pass["scores"].get(framework_id, 0) for framework_id in ACTIVE_FRAMEWORK_IDS}
    criteria = []

    if tokens & RELATIONSHIP_TERMS:
        scores["swot"] += 4
        criteria.append("Personal or relationship decisions require a diagnostic audit before advice.")
    if any(word in tokens for word in ["rank", "prioritize", "features", "score", "backlog"]):
        scores["rice"] += 3
        criteria.append("Ranking language gets extra weight for RICE.")
    if any(word in tokens for word in ["validate", "mvp", "experiment", "traction"]):
        scores["lean_startup"] += 3
        criteria.append("Validation language gets extra weight for Lean Startup.")
    if any(word in tokens for word in ["commercialize", "commercialization", "monetize", "pilot", "buyer"]):
        scores["lean_startup"] += 4
        criteria.append(f"{brief.subject[:1].upper()}{brief.subject[1:]} requires pilot evidence before scaling.")
    if any(word in tokens for word in ["industry", "supplier", "buyer", "substitute", "entrant", "rivalry"]):
        scores["porters_five_forces"] += 3
        criteria.append("Industry-structure language gets extra weight for Porter's Five Forces.")
    if any(word in tokens for word in ["legal", "regulatory", "global", "policy", "economic", "environmental"]):
        scores["pestle"] += 3
        criteria.append("Macro-environment language gets extra weight for PESTLE.")
    if any(word in tokens for word in ["lighter", "stronger", "cheaper", "faster", "constraint", "contradiction", "material"]):
        scores["triz"] += 3
        criteria.append("Physical or engineering tradeoff language gets extra weight for TRIZ.")
    if any(word in tokens for word in ["okr", "objectives", "quarterly", "alignment", "key"]):
        scores["okrs"] += 3
        criteria.append("Measurable alignment language gets extra weight for OKRs.")

    if "market" in tokens and "enter" in tokens:
        scores["swot"] += 2
        criteria.append("Market-entry ambiguity keeps SWOT competitive unless industry forces dominate.")
    if "five forces" in text:
        scores["porters_five_forces"] += 6
        criteria.append("Explicit framework mention overrides nearby generic strategy language.")

    winner = max(scores, key=scores.get)
    top_score = scores[winner]
    sorted_scores = sorted(scores.values(), reverse=True)
    margin = top_score - (sorted_scores[1] if len(sorted_scores) > 1 else 0)
    confidence = min(0.96, 0.62 + top_score * 0.025 + margin * 0.035)
    return {
        "name": "Adjudicator criteria",
        "winner": winner,
        "winner_name": FRAMEWORK_NAMES.get(winner, winner),
        "scores": scores,
        "confidence": round(confidence, 2),
        "signals": criteria[:4] or ["Combined score selected the most reasonable execution path."],
    }


def smart_criteria_route(goal: str) -> RouteDecision:
    brief = extract_domain_brief(goal)
    intent_pass = _score_pass(goal, "intent")
    output_pass = _score_pass(goal, "output")
    mismatch = intent_pass["winner"] != output_pass["winner"]
    adjudicator = _adjudicate_smart_passes(goal, intent_pass, output_pass) if mismatch else None
    selected_pass = adjudicator or intent_pass
    framework_id = selected_pass["winner"]
    agreement_text = (
        f"Both smart-criteria passes selected {FRAMEWORK_NAMES.get(framework_id, framework_id)}."
        if not mismatch
        else f"Intent selected {intent_pass['winner_name']} while output-fit selected {output_pass['winner_name']}; adjudicator selected {selected_pass['winner_name']}."
    )
    rationale = {
        "swot": f"SWOT was selected to audit the controllable strengths, gaps, market openings, and threats around {brief.subject}, especially for {brief.users}.",
        "rice": f"RICE was selected to rank the next initiatives for {brief.subject} by reach, impact, confidence, and effort.",
        "triz": f"TRIZ was selected because {brief.subject} contains a design contradiction where improving one property may worsen another.",
        "lean_startup": f"Lean Startup was selected because {brief.subject} needs a falsifiable pilot, buyer proof, and measurable evidence before heavy commercialization investment.",
        "okrs": f"OKRs were selected because {brief.subject} needs measurable objectives, key results, and operating cadence.",
        "porters_five_forces": f"Porter's Five Forces was selected because {brief.subject} depends on industry structure, substitutes, buyer power, supplier power, and competitive pressure.",
        "pestle": f"PESTLE was selected because {brief.subject} depends on macro political, economic, social, technological, legal, or environmental forces.",
    }[framework_id]
    return {
        "framework_id": framework_id,
        "confidence": selected_pass["confidence"],
        "rationale": f"{agreement_text} {rationale}",
        "selection_process": {
            "summary": agreement_text,
            "passes": [intent_pass, output_pass] + ([adjudicator] if adjudicator else []),
            "mismatch_resolved": mismatch,
            "selected_framework": framework_id,
            "domain_brief": {
                "subject": brief.subject,
                "domain": brief.domain,
                "users": brief.users,
                "workflow": brief.workflow,
                "value_hypothesis": brief.value_hypothesis,
                "constraints": brief.constraints,
                "proof_metrics": brief.proof_metrics,
            },
        },
    }


def deterministic_route(goal: str) -> RouteDecision:
    return smart_criteria_route(goal)


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
                "selection_process": {
                    "summary": "LLM route reinforcement pass.",
                    "passes": [],
                    "mismatch_resolved": False,
                    "selected_framework": parsed["framework_id"],
                },
            }
    except Exception:
        return None

    return None


async def langchain_enrich_canvas(framework_id: str, goal: str, canvas: dict, provider: str | None = None, model_id: str | None = None) -> dict | None:
    prompt = (
        "You are OmniFrame's senior framework analyst with web research enabled when available. Return only valid JSON.\n"
        "Preserve the current canvas schema and top-level type exactly, but rewrite generic content into concrete, domain-specific analysis.\n"
        "Use the user's exact context, names, constraints, and emotional/business/engineering details. If the prompt is personal or relationship-related, avoid business jargon.\n"
        "The root canvas must already feel complete before the user opens any focus workspace: populate every first-page section, row, force, objective, lane, or principle with highly specific wording tied to the user's prompt.\n"
        "Do not reserve all specificity for drilldowns. The first screen should give a panoramic view of user focus, derived context, key variables, risks, and next moves.\n"
        "For relationship decisions, do not decide for the user; organize values, patterns, boundaries, repair options, safety concerns, and conversation experiments.\n"
        "For every drilldown panel, provide options that directly reference the original user input and the current framework.\n"
        "For every option set, keep options specific to that panel's role: evidence options must be evidence, actions must be actions, metrics must be metrics, risks must be risks, and experiments must be experiments.\n"
        "Use reputable public web context where useful, but do not include citations in the JSON unless a field already supports them.\n\n"
        f"Framework: {framework_id}\n"
        f"Goal: {goal}\n"
        f"Current canvas JSON:\n{json.dumps(canvas)}"
    )
    parsed = await _llm_json(prompt, provider, model_id)
    if isinstance(parsed, dict) and parsed.get("type") == canvas.get("type"):
        return parsed
    return None


def _fallback_option_sets(
    panel_kind: str,
    focus_title: str,
    panel_title: str,
    panel_value: str | None = None,
    refresh_round: int = 0,
    goal: str = "",
) -> list[list[str]]:
    subject = re.sub(r"\s+", " ", focus_title.strip())[:160]
    value_hint = re.sub(r"\s+", " ", (panel_value or "").strip())[:120]
    reference = value_hint or subject
    brief = extract_domain_brief(goal or focus_title)

    if "CNC" in brief.domain or "CNC" in brief.subject:
        by_kind = {
            "evidence": [
                [
                    "Benchmark the optimized CNC/CAM file against the original for cycle time, air cuts, tool changes, and machine-hour cost.",
                    "Run the output through simulation/backplotting before any live machining trial.",
                    "Ask 5 CAM programmers which toolpath changes they would trust without manual rewrite.",
                ],
                [
                    "Compare the algorithm against one manual machinist edit and one CAM-system optimization feature.",
                    "Collect before/after evidence for surface finish, scrap risk, and tool-wear cost.",
                    "Log every unsafe, incompatible, or low-confidence toolpath recommendation.",
                ],
                [
                    "Use anonymized G-code/CAM examples from at least three materials or part families.",
                    "Measure whether the optimized file preserves tolerances, fixtures, and controller/post-processor assumptions.",
                    "Document the evidence a job shop owner would need before paying for a pilot.",
                ],
            ],
            "action": [
                [
                    "Create a 7-day pilot offer: submit one CNC file, receive an optimized version, simulation report, ROI estimate, and risk notes.",
                    "Package the algorithm as a reviewed recommendation engine before letting it rewrite production files automatically.",
                    "Choose one buyer wedge: job shops with high spindle-hour costs, CAM programmers with repetitive files, or quoting teams needing faster estimates.",
                ],
                [
                    "Build a before/after demo using a representative CNC file and show cycle-time savings with the exact toolpath changes highlighted.",
                    "Add a confidence gate: auto-suggest low-risk improvements, require human review for risky feed/speed or geometry changes.",
                    "Interview manufacturing engineers about integration requirements for Fusion, Mastercam, Siemens NX, Haas, Fanuc, or their current controller stack.",
                ],
            ],
            "metric": [
                [
                    "Cycle-time reduction versus the baseline CNC/CAM file.",
                    "Successful simulation or dry-run pass rate.",
                    "Machine-hour ROI per optimized job.",
                ],
                [
                    "Tool-wear cost reduction after optimization.",
                    "Scrap or rework rate after optimized file use.",
                    "Pilot buyer willingness-to-pay after reviewing the before/after report.",
                ],
                [
                    "Percentage of recommendations accepted by a CAM programmer without manual correction.",
                    "Number of controller/post-processor incompatibilities found before live machining.",
                    "Time from file upload to trusted optimization report.",
                ],
            ],
            "risk": [
                [
                    "A single unsafe toolpath could damage a machine, scrap a part, or destroy buyer trust.",
                    "Controller/post-processor differences can make a good optimization unsafe on another machine.",
                    "Customers may refuse to upload proprietary part files without on-prem, deletion, or anonymization controls.",
                ],
                [
                    "The algorithm may optimize cycle time while worsening surface finish, tolerances, or tool life.",
                    "CAM vendors may already own the integration surface and can copy obvious optimization features.",
                    "The buyer may see the result as consulting, not repeatable software, unless the workflow is packaged clearly.",
                ],
            ],
            "experiment": [
                [
                    "Run a concierge pilot on 10 anonymized CNC files: baseline, optimized output, simulation result, machinist review, ROI estimate.",
                    "Test one material and one machine/controller class before claiming broad CNC compatibility.",
                    "Use a human review gate for every optimized file until unsafe recommendation rate is below a written threshold.",
                ],
                [
                    "Offer three job shops a no-risk benchmark: pay only if cycle time or tooling-cost savings exceed a pre-agreed threshold.",
                    "Run A/B quoting: current manual estimate versus algorithm-assisted estimate for time and accuracy.",
                    "Measure whether CAM programmers request a second file optimization after the first report.",
                ],
            ],
            "definition": [
                [
                    "Define the V1 as: upload CNC/CAM file, detect safe optimization opportunities, generate a simulation-ready report, and require human approval before production use.",
                    "Exclude full autonomous machine control from V1; focus on trusted recommendations and validated file changes.",
                    "Specify supported inputs first: G-code, CAM export, controller type, material, tool library, and machine constraints.",
                ],
                [
                    "Define the buyer promise as reducing machine time or programming effort without increasing scrap, tool wear, or machine-crash risk.",
                    "Make the acceptance condition: the optimized file passes simulation and a CAM programmer accepts the recommendation.",
                    "State the edge cases V1 will refuse: unknown controller, missing tool data, tight tolerance risk, or unsafe geometry assumptions.",
                ],
            ],
        }
        options = by_kind.get(panel_kind, by_kind["action"])
        start = refresh_round % len(options)
        return options[start:] + options[:start]

    by_kind = {
        "evidence": [
            [
                f"Find one direct observation that supports or weakens: {reference}.",
                "Ask for examples rather than opinions from the most relevant people.",
                "Separate firsthand evidence from assumptions, hopes, or inherited advice.",
            ],
            [
                "Name the evidence that would make you reverse this belief.",
                "Look for one counterexample before treating the claim as settled.",
                "Compare the claim against a past pattern, logged behavior, or external data point.",
            ],
            [
                f"Create an evidence log for '{subject}' with source, date, confidence, and what it changes.",
                "Use one outside reference point and one firsthand signal before accepting the option.",
                "Mark each signal as confirming, weakening, or irrelevant to the current decision.",
            ],
            [
                f"Ask what would make this panel's claim false for: {reference}.",
                "Collect a behavioral example from the last 30 days instead of relying on a summary judgment.",
                "Distinguish preference evidence from compatibility, demand, risk, or execution evidence.",
            ],
        ],
        "action": [
            [
                f"Turn '{subject}' into one reversible next move.",
                "Set a clear owner, deadline, and smallest visible output.",
                "Choose the step that creates new information without overcommitting.",
            ],
            [
                "Convert the insight into a short conversation, prototype, or decision memo.",
                "Decide what should stop while this move is tested.",
                "Write the trigger that tells you to continue, revise, or abandon the move.",
            ],
            [
                f"Choose one next action for '{reference}' that can be done without locking in the final decision.",
                "Write the decision rule before taking the action so the result cannot be rationalized later.",
                "Make the move small enough to complete before the next review window.",
            ],
            [
                f"Convert this panel into a concrete ask, prototype, outreach, or conversation tied to '{subject}'.",
                "Pair the action with one constraint: time box, budget cap, or emotional safety boundary.",
                "Define who must respond, what must be observed, and what happens immediately after.",
            ],
        ],
        "metric": [
            [
                f"Observable change connected to: {subject}.",
                "Decision confidence before versus after the next action.",
                "Number of concrete signals collected, reviewed, and acted on.",
            ],
            [
                "A pass/fail threshold written before the next experiment starts.",
                "Frequency of the desired behavior or outcome over the next review window.",
                "Time from insight to decision-ready evidence.",
            ],
            [
                f"Count of high-quality signals gathered for '{reference}' before the next decision checkpoint.",
                "Percentage of selected options that produce clear evidence instead of more ambiguity.",
                "A written confidence score with one sentence explaining why it moved.",
            ],
            [
                f"Review-window trend for the behavior, demand, constraint, or outcome behind '{subject}'.",
                "Number of assumptions converted into pass, fail, or still-unknown status.",
                "Time spent debating versus time spent collecting useful signals.",
            ],
        ],
        "risk": [
            [
                f"The plan fails if the main assumption behind '{subject}' is false.",
                "The next action produces noise instead of decision-grade evidence.",
                "The move reduces one risk while quietly increasing another.",
            ],
            [
                "A short-term improvement hides a deeper constraint.",
                "The process becomes performative because no decision threshold exists.",
                "The wrong stakeholder or signal dominates the conclusion.",
            ],
            [
                f"The new option may optimize '{reference}' while ignoring the larger decision context.",
                "Repeated regeneration can become avoidance if no option is selected and tested.",
                "The safest-looking option may preserve the current problem rather than resolve it.",
            ],
            [
                f"The panel can drift away from '{subject}' if the next step is not tied to observable evidence.",
                "A strong emotional reaction or stakeholder preference can be mistaken for proof.",
                "A single positive signal can hide unresolved constraints or incompatibilities.",
            ],
        ],
        "experiment": [
            [
                f"Run a small test that isolates the assumption inside: {subject}.",
                "Define baseline, test variant, review date, and stop condition.",
                "Use a manual version first if automation or commitment would be premature.",
            ],
            [
                "Choose a 7-day version that creates evidence without locking in the final path.",
                "Record what counts as a pass, partial pass, and clear fail.",
                "Keep the experiment narrow enough that one result actually means something.",
            ],
            [
                f"Design a two-option test for '{reference}' so the result can compare alternatives, not just feelings.",
                "Keep the test reversible and write down what would make you stop early.",
                "Capture the result in the report as baseline, intervention, signal, and decision.",
            ],
            [
                f"Run the smallest real-world version of '{subject}' with one measurable outcome.",
                "Avoid testing multiple changes at once unless the goal is exploration rather than proof.",
                "Schedule the review before starting so the experiment cannot expand indefinitely.",
            ],
        ],
        "contradiction": [
            [
                f"I want to improve '{subject}' without worsening the most important constraint.",
                "Name the property that must improve and the property that cannot be sacrificed.",
                "Rewrite the conflict as a single sentence with both sides visible.",
            ],
            [
                "Separate the visible symptom from the underlying tradeoff.",
                "State what gets better, what gets worse, and why the current approach couples them.",
                "Define the contradiction so a prototype can test it rather than debate it.",
            ],
            [
                f"The current approach links '{reference}' to an unwanted cost, delay, risk, or loss of clarity.",
                "Rewrite the tradeoff as improve X while preserving Y.",
                "Name what would prove the contradiction has been uncoupled.",
            ],
            [
                f"Identify whether '{subject}' is a real contradiction, a missing constraint, or a vague preference conflict.",
                "State the hidden assumption that makes both sides feel mutually exclusive.",
                "Choose one principle that can separate the two sides into different times, places, parts, or rules.",
            ],
        ],
        "definition": [
            [
                f"Rewrite '{subject}' as a concrete requirement with user, trigger, behavior, and outcome.",
                "Cut wording that does not change the build, decision, or test.",
                "Name the smallest version that still proves the core value.",
            ],
            [
                "Describe who uses it, what they do, and how success is visible.",
                "Separate required behavior from polish, automation, or nice-to-have scope.",
                "Add one explicit non-goal so scope does not expand silently.",
            ],
            [
                f"Define '{reference}' as a job, actor, input, output, and acceptance condition.",
                "Write the smallest version that a real user or stakeholder could react to.",
                "Name what this definition deliberately excludes for now.",
            ],
            [
                f"Turn '{subject}' into one sentence that can be scored, tested, or assigned.",
                "Replace adjectives with observable behavior or measurable thresholds.",
                "State the edge case that would break this definition.",
            ],
        ],
    }
    options = by_kind.get(panel_kind, by_kind["action"])
    if not options:
        return []
    start = refresh_round % len(options)
    return options[start:] + options[:start]


async def refresh_panel_options(request, provider: str | None = None, model_id: str | None = None) -> dict:
    panel_kind = request.panel_kind or "action"
    prompt = (
        "You are OmniFrame's focused option generator. Return only valid JSON in this exact shape: "
        '{"option_sets":[["option one","option two","option three"],["option one","option two","option three"]]}.\n'
        "Generate fresh, non-duplicative options for the specified panel only. "
        "Every option must match the panel purpose. Evidence panels need proof/validation options; action panels need concrete moves; "
        "metric panels need observable measurements; risk panels need failure modes; experiment panels need tests; definition panels need requirements. "
        "Do not reuse the existing options. Do not include generic placeholders.\n\n"
        f"Framework: {request.framework_id}\n"
        f"Goal: {request.goal}\n"
        f"Focus title: {request.focus_title}\n"
        f"Focus description: {request.focus_description or ''}\n"
        f"Panel title: {request.panel_title}\n"
        f"Panel kind: {panel_kind}\n"
        f"Panel prompt: {request.panel_prompt or ''}\n"
        f"Current note: {request.panel_value or ''}\n"
        f"Refresh round: {request.refresh_round}\n"
        f"Existing options to avoid: {json.dumps(request.existing_options[:50])}"
    )
    parsed = await _llm_json(prompt, provider, model_id)
    option_sets = parsed.get("option_sets") if isinstance(parsed, dict) else None
    if isinstance(option_sets, list):
        cleaned_sets: list[list[str]] = []
        seen: set[str] = set()
        for option_set in option_sets:
            if not isinstance(option_set, list):
                continue
            cleaned = [str(option).strip()[:240] for option in option_set if str(option).strip()]
            cleaned = [option for option in cleaned if option.lower() not in seen]
            seen.update(option.lower() for option in cleaned)
            if len(cleaned) >= 2:
                cleaned_sets.append(cleaned[:4])
        if cleaned_sets:
            return {"option_sets": cleaned_sets[:4]}
    return {"option_sets": _fallback_option_sets(panel_kind, request.focus_title, request.panel_title, request.panel_value, request.refresh_round, request.goal)}


async def route_goal(goal: str, framework_id: str | None = None, model_provider: str | None = None, model_id: str | None = None) -> dict:
    smart_decision = deterministic_route(goal)
    llm_decision = await langchain_route(goal, model_provider, model_id)

    if framework_id:
        framework = get_framework(framework_id)
        if not framework or framework_id not in ACTIVE_FRAMEWORK_IDS:
            decision = smart_decision
        else:
            canvas = build_canvas(framework_id, goal)
            enriched = await langchain_enrich_canvas(framework_id, goal, canvas, model_provider, model_id)
            selection_process = {
                **smart_decision["selection_process"],
                "summary": f"Smart criteria recommended {FRAMEWORK_NAMES.get(smart_decision['framework_id'], smart_decision['framework_id'])}; user overrode to {framework['name']}.",
                "user_override": {
                    "recommended_framework": smart_decision["framework_id"],
                    "selected_framework": framework_id,
                    "reason": "User chose a different live route after reviewing the recommendation.",
                },
            }
            if llm_decision:
                selection_process["reinforcer"] = {
                    "framework_id": llm_decision["framework_id"],
                    "framework_name": FRAMEWORK_NAMES.get(llm_decision["framework_id"], llm_decision["framework_id"]),
                    "confidence": llm_decision["confidence"],
                    "rationale": llm_decision["rationale"],
                }
            return {
                "framework_id": framework_id,
                "framework_name": framework["name"],
                "confidence": 1.0,
                "rationale": f"User selected {framework['name']} after reviewing OmniFrame's recommendation.",
                "selection_process": selection_process,
                "canvas": enriched or canvas,
            }
    else:
        decision = smart_decision

    selection_process = dict(decision["selection_process"])
    if llm_decision:
        selection_process["reinforcer"] = {
            "framework_id": llm_decision["framework_id"],
            "framework_name": FRAMEWORK_NAMES.get(llm_decision["framework_id"], llm_decision["framework_id"]),
            "confidence": llm_decision["confidence"],
            "rationale": llm_decision["rationale"],
            "agreement": llm_decision["framework_id"] == decision["framework_id"],
        }
        if llm_decision["framework_id"] != decision["framework_id"]:
            selection_process["summary"] = (
                f"{selection_process.get('summary', '')} LLM reinforcement preferred "
                f"{FRAMEWORK_NAMES.get(llm_decision['framework_id'], llm_decision['framework_id'])}, but the criteria adjudicator retained "
                f"{FRAMEWORK_NAMES.get(decision['framework_id'], decision['framework_id'])}."
            ).strip()

    framework = get_framework(decision["framework_id"])
    if not framework:
        decision = smart_decision
        framework = get_framework(decision["framework_id"])
        selection_process = dict(decision["selection_process"])

    canvas = build_canvas(decision["framework_id"], goal)
    enriched = await langchain_enrich_canvas(decision["framework_id"], goal, canvas, model_provider, model_id)
    return {
        "framework_id": decision["framework_id"],
        "framework_name": framework["name"],
        "confidence": decision["confidence"],
        "rationale": decision["rationale"],
        "selection_process": selection_process,
        "canvas": enriched or canvas,
    }
