"""One-shot generator for framework catalog component arrays."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

CATALOG_PATH = Path(__file__).resolve().parents[1] / "backend" / "app" / "data" / "framework_catalog.json"

COMPONENT_OVERRIDES: dict[str, list[str]] = {
    "okrs": ["Objectives", "Key Results"],
    "tam_sam_som": [
        "Total Addressable Market",
        "Serviceable Addressable Market",
        "Obtainable Market",
    ],
    "stage_gate": [
        "Discovery",
        "Scoping",
        "Business Case",
        "Development",
        "Testing and Validation",
        "Launch",
        "Post-Launch Review",
    ],
    "innovators_dilemma": [
        "Sustaining Innovation",
        "Disruptive Innovation",
        "Value Networks",
    ],
    "first_principles": ["Deconstruct Assumptions", "Rebuild from First Principles"],
    "tows": ["SO Strategies", "ST Strategies", "WO Strategies", "WT Strategies"],
    "hoshin_kanri": [
        "Long-Term Goals",
        "Annual Objectives",
        "Top-Level Priorities",
        "Targets to Improve",
    ],
    "wardley_mapping": ["Value Chain", "Evolution Stage"],
    "triz": ["Inventive Principles", "Contradiction Matrix"],
    "six_thinking_hats": [
        "White Hat",
        "Red Hat",
        "Black Hat",
        "Yellow Hat",
        "Green Hat",
        "Blue Hat",
    ],
    "odi": ["Desired Outcomes", "Opportunity Algorithm"],
    "ends_ways_means": ["Ends", "Ways", "Means"],
    "mdmp": [
        "Receipt of Mission",
        "Mission Analysis",
        "COA Development",
        "COA Analysis",
        "COA Comparison",
        "COA Approval",
        "Orders Production",
    ],
    "metl": ["Mission-Essential Tasks", "Supporting Tasks", "Training Standards"],
    "fast_value_engineering": [
        "Function Definition",
        "FAST Diagram",
        "Value and Cost Analysis",
    ],
    "jcids": ["Capability Gap", "Requirements", "Solution Analysis", "Validation"],
    "big_data_8_step": [
        "Question",
        "Dictionaries",
        "Rules",
        "Gather",
        "Analyze",
        "Decide",
        "Validate",
        "Communicate",
    ],
}

# Richer seed content for live routes and common component labels.
COMPONENT_SEEDS: dict[str, dict[str, dict[str, Any]]] = {
    "swot": {
        "strengths": {
            "description": "Internal capabilities, assets, and advantages that support the decision or strategy.",
            "prompt": "Name specific internal strengths tied to the user's goal—not generic traits.",
            "questions": [
                "What unique assets, skills, or relationships can we leverage?",
                "Which advantages are durable versus temporary?",
                "What evidence supports each claimed strength?",
                "How does each strength connect to the desired outcome?",
            ],
        },
        "weaknesses": {
            "description": "Internal limitations, gaps, or constraints that could undermine execution.",
            "prompt": "Surface honest internal weaknesses that are specific to this context.",
            "questions": [
                "What internal gaps could slow or distort the decision?",
                "Which weaknesses are fixable in the near term versus structural?",
                "What habits, missing evidence, or trust gaps matter here?",
                "How might each weakness interact with external threats?",
            ],
        },
        "opportunities": {
            "description": "External openings, timing advantages, or favorable conditions to exploit.",
            "prompt": "Identify external opportunities the user could realistically act on.",
            "questions": [
                "What external tailwinds or openings are visible now?",
                "Which partnerships, channels, or timing windows matter?",
                "What customer or user improvements become possible?",
                "What would confirm an opportunity is real versus imagined?",
            ],
        },
        "threats": {
            "description": "External risks, competitive pressures, or failure modes that could reduce success.",
            "prompt": "Name credible external threats tied to the user's specific situation.",
            "questions": [
                "What substitutes, competitors, or regulatory risks apply?",
                "Which timing or switching risks could block progress?",
                "What social, legal, or technical risks are most plausible?",
                "What early warning signals would indicate a threat is materializing?",
            ],
        },
    },
    "lean_startup": {
        "build_measure_learn": {
            "description": "The iterative cycle of building a test artifact, measuring behavior, and learning what to do next.",
            "prompt": "Define the smallest Build-Measure-Learn loop that tests the riskiest assumption.",
            "questions": [
                "What is the riskiest assumption that must be tested first?",
                "What is the smallest artifact or concierge workflow to test it?",
                "What behavior signal will prove or disprove the assumption?",
                "What pivot, persevere, or stop rule applies after the test?",
            ],
        },
        "mvp": {
            "description": "The minimum viable product—the smallest deliverable that enables validated learning.",
            "prompt": "Define an MVP narrow enough to run quickly but rich enough to produce behavior data.",
            "questions": [
                "What is the smallest version that still tests the core hypothesis?",
                "Which features are excluded to preserve speed and clarity?",
                "Who is the first user cohort and what will they actually do?",
                "How will success or failure be measured within days, not months?",
            ],
        },
        "actionable_metrics": {
            "description": "Metrics tied to real user behavior and decision thresholds, not vanity counts.",
            "prompt": "Choose metrics that drive a clear learn-or-pivot decision.",
            "questions": [
                "Which metric reflects meaningful behavior rather than interest?",
                "What baseline exists today for that metric?",
                "What threshold would justify scaling, pivoting, or stopping?",
                "How will the metric be collected without biasing the experiment?",
            ],
        },
    },
    "okrs": {
        "objectives": {
            "description": "Qualitative, directional goals that describe what success should feel like.",
            "prompt": "Write objectives that are ambitious, specific to the domain, and free of metric laundry lists.",
            "questions": [
                "What outcome would make this quarter meaningfully different?",
                "Is the objective directional without smuggling in the metrics?",
                "Does the objective connect to the user's stated goal and constraints?",
                "Would teams know when they are off-track from the wording alone?",
            ],
        },
        "key_results": {
            "description": "Measurable, time-bound results that prove an objective was achieved.",
            "prompt": "Define key results that are measurable, behavior-based, and hard to game.",
            "questions": [
                "What number or observable outcome proves progress?",
                "Are the key results outcome-based rather than output-based?",
                "What evidence threshold defines green, yellow, and red?",
                "Which initiatives could plausibly move each key result?",
            ],
        },
    },
    "porters_five_forces": {
        "rivalry": {
            "description": "Intensity of competition among existing players in the market.",
            "prompt": "Assess rivalry with named competitors or competitor categories from the user's domain.",
            "questions": [
                "Who are the direct rivals and how aggressively do they compete on price or features?",
                "Is the market fragmented or dominated by a few players?",
                "What switching costs or differentiation reduce rivalry pressure?",
                "Does rivalry create moat, margin pressure, or distribution constraints?",
            ],
        },
        "new_entrants": {
            "description": "Ease with which new competitors can enter and disrupt the space.",
            "prompt": "Evaluate barriers to entry and plausible new-entrant threats.",
            "questions": [
                "What capital, regulation, or network effects block new entrants?",
                "Which adjacent players could enter with minimal repositioning?",
                "How fast could a well-funded entrant replicate the core offer?",
                "What wedge would a new entrant use against incumbents?",
            ],
        },
        "substitutes": {
            "description": "Alternative solutions that satisfy the same job with different means.",
            "prompt": "Identify substitutes customers use today, including manual workarounds.",
            "questions": [
                "What do users do when they do not choose this category at all?",
                "Which substitutes are improving faster than the core offer?",
                "Where is switching to a substitute easy or habitual?",
                "What price or performance gap would trigger substitution?",
            ],
        },
        "buyer_power": {
            "description": "Leverage customers have to demand lower prices or better terms.",
            "prompt": "Analyze buyer concentration, alternatives, and price sensitivity.",
            "questions": [
                "How concentrated are buyers and how easy is comparison shopping?",
                "What information or switching costs reduce buyer power?",
                "Can buyers integrate backward or build in-house alternatives?",
                "Which buyer segments have the most negotiating leverage?",
            ],
        },
        "supplier_power": {
            "description": "Leverage upstream providers have over cost, quality, or availability.",
            "prompt": "Map critical suppliers and their ability to capture value.",
            "questions": [
                "Which inputs are scarce, specialized, or single-sourced?",
                "Can suppliers forward-integrate or bypass the user's position?",
                "How replaceable are the most important suppliers?",
                "What contractual or technical mitigations reduce supplier power?",
            ],
        },
    },
    "pestle": {
        "political": {
            "description": "Government policy, stability, trade rules, and political incentives affecting the domain.",
            "prompt": "Identify political forces tailored to the user's geography and industry.",
            "questions": [
                "Which policies, subsidies, or sanctions could help or hurt this effort?",
                "How stable is the relevant political environment over the planning horizon?",
                "Are there lobbying, compliance, or procurement politics to monitor?",
                "What political signals would trigger a strategy change?",
            ],
        },
        "economic": {
            "description": "Macroeconomic conditions, funding climate, and cost structures shaping viability.",
            "prompt": "Assess economic tailwinds and headwinds for the specific market.",
            "questions": [
                "How do interest rates, inflation, or spending cycles affect demand?",
                "What budget constraints do target buyers face?",
                "Which cost inputs are most volatile?",
                "What economic indicator would confirm timing to act or wait?",
            ],
        },
        "social": {
            "description": "Demographic, cultural, and behavioral trends influencing adoption or perception.",
            "prompt": "Connect social trends to how users actually behave in this domain.",
            "questions": [
                "Which demographic or cultural shifts change willingness to adopt?",
                "What norms or stigma could accelerate or block uptake?",
                "How do community or workforce attitudes affect execution?",
                "What social proof would increase trust?",
            ],
        },
        "technological": {
            "description": "Technology shifts, platform changes, and innovation pace relevant to the problem.",
            "prompt": "Map technology forces that enable, commoditize, or obsolete parts of the plan.",
            "questions": [
                "Which emerging technologies reduce cost or unlock new capabilities?",
                "Where is the relevant tech moving from custom to commodity?",
                "What technical dependencies could break or accelerate the roadmap?",
                "Which standards or platform shifts require early positioning?",
            ],
        },
        "legal": {
            "description": "Laws, regulations, liability, and compliance obligations in scope.",
            "prompt": "Surface legal constraints and compliance triggers specific to the domain.",
            "questions": [
                "Which regulations directly govern this product or workflow?",
                "What licensing, privacy, or liability rules affect launch timing?",
                "Are pending legal changes likely to help or constrain the plan?",
                "What compliance evidence must exist before scaling?",
            ],
        },
        "environmental": {
            "description": "Climate, sustainability, resource, and environmental constraints or opportunities.",
            "prompt": "Evaluate environmental factors that affect operations, perception, or regulation.",
            "questions": [
                "Which environmental regulations or reporting duties apply?",
                "How do climate or resource risks affect supply or operations?",
                "Could sustainability positioning create advantage or requirement?",
                "What environmental metrics matter to buyers or regulators?",
            ],
        },
    },
    "rice": {
        "reach": {
            "description": "How many users or events the initiative affects in a given time period.",
            "prompt": "Estimate reach with explicit assumptions tied to the user's audience.",
            "questions": [
                "How many users, accounts, or events will this affect per month or quarter?",
                "Which segment defines the reach numerator?",
                "What data supports the reach estimate?",
                "How sensitive is priority to a 2x error in reach?",
            ],
        },
        "impact": {
            "description": "Expected magnitude of outcome improvement if the initiative succeeds.",
            "prompt": "Score impact based on concrete outcome movement, not enthusiasm.",
            "questions": [
                "What outcome metric would move and by roughly how much?",
                "Is impact measured per user, per account, or per transaction?",
                "What would a minimal, moderate, and massive impact look like?",
                "How does impact compare across competing initiatives?",
            ],
        },
        "confidence": {
            "description": "Degree of certainty that reach, impact, and effort estimates are accurate.",
            "prompt": "Justify confidence with evidence, prototypes, or analogous cases.",
            "questions": [
                "What evidence already exists for reach and impact assumptions?",
                "Which parts of the estimate are guesswork versus measured?",
                "What quick test would raise confidence before full build?",
                "What confidence level still justifies proceeding?",
            ],
        },
        "effort": {
            "description": "Total person-time or calendar time required to deliver the initiative.",
            "prompt": "Estimate effort including design, build, rollout, and operational cost.",
            "questions": [
                "How many person-weeks or person-months are required end to end?",
                "Which dependencies inflate effort beyond engineering alone?",
                "What scope reduction would cut effort materially?",
                "Does effort include maintenance and support after launch?",
            ],
        },
    },
    "triz": {
        "inventive_principles": {
            "description": "TRIZ inventive principles that resolve contradictions through proven patterns of innovation.",
            "prompt": "Select principles that translate into concrete design or process moves in the user's domain.",
            "questions": [
                "Which contradiction is blocking progress today?",
                "Which inventive principles map cleanly to this contradiction?",
                "How would each principle change structure, timing, materials, or interfaces?",
                "What prototype would prove a principle actually helps?",
            ],
        },
        "contradiction_matrix": {
            "description": "The paired tension between improving one parameter while worsening another.",
            "prompt": "State the contradiction in domain language: improve X without worsening Y.",
            "questions": [
                "What parameter must improve and what parameter gets worse when you try?",
                "Is the conflict technical, physical, or organizational?",
                "Which TRIZ parameter labels best describe the tradeoff?",
                "What failure modes appear if the contradiction is ignored?",
            ],
        },
    },
}

LABEL_ALIASES: dict[str, str] = {
    "Build-Measure-Learn": "build_measure_learn",
    "MVP": "mvp",
    "actionable metrics": "actionable_metrics",
    "Rivalry": "rivalry",
    "new entrants": "new_entrants",
    "substitutes": "substitutes",
    "buyer power": "buyer_power",
    "supplier power": "supplier_power",
    "Political": "political",
    "Economic": "economic",
    "Social": "social",
    "Technological": "technological",
    "Legal": "legal",
    "Environmental": "environmental",
    "Reach": "reach",
    "Impact": "impact",
    "Confidence": "confidence",
    "Effort": "effort",
    "Strengths": "strengths",
    "Weaknesses": "weaknesses",
    "Opportunities": "opportunities",
    "Threats": "threats",
    "Objectives": "objectives",
    "Key Results": "key_results",
    "Inventive Principles": "inventive_principles",
    "contradiction matrix": "contradiction_matrix",
}


def slugify(label: str) -> str:
    normalized = label.lower()
    normalized = normalized.replace("&", "and")
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    return normalized.strip("_")


def component_id(framework_id: str, label: str) -> str:
    alias = LABEL_ALIASES.get(label)
    if alias:
        return alias
    return slugify(label)


def parse_labels(framework: dict[str, Any]) -> list[str]:
    framework_id = framework["id"]
    if framework_id in COMPONENT_OVERRIDES:
        return COMPONENT_OVERRIDES[framework_id]
    return [part.strip() for part in framework["core_components"].split(",") if part.strip()]


def generic_component(
    framework: dict[str, Any],
    label: str,
    comp_id: str,
) -> dict[str, Any]:
    name = framework["name"]
    lens = framework["selection_lens"]
    lower = label.lower()

    description = (
        f"In {name}, {label} is a core lens for examining the problem through that framework's structure."
    )
    prompt = (
        f"Analyze {lower} in direct relation to the user's goal. {lens.rstrip('.')}."
    )

    questions = [
        f"What does {lower} look like in this specific situation?",
        f"Which evidence would confirm or challenge our read on {lower}?",
        f"How does {lower} interact with other parts of {name}?",
        f"What decision or next action follows from what we learn about {lower}?",
    ]

    if any(word in lower for word in ("risk", "threat", "weakness", "obstacle", "vulnerability")):
        questions[1] = f"What is the most credible way {lower} could materialize here?"
        questions[3] = f"What mitigation or monitoring should we put in place for {lower}?"
    elif any(word in lower for word in ("strength", "opportunity", "advantage", "benefit")):
        questions[1] = f"What proof shows this {lower} is real rather than assumed?"
        questions[3] = f"How can we act on {lower} within current constraints?"
    elif any(word in lower for word in ("metric", "measure", "result", "revenue", "retention")):
        questions[1] = f"What baseline and target define success for {lower}?"
        questions[2] = f"Which behaviors or events should move {lower}?"
    elif any(word in lower for word in ("strategy", "approach", "method", "tactic", "way")):
        questions[1] = f"Which alternatives exist for executing {lower}?"
        questions[2] = f"What resources or dependencies does {lower} require?"

    return {
        "id": comp_id,
        "label": label,
        "description": description,
        "prompt": prompt,
        "questions": questions,
    }


def build_component(framework: dict[str, Any], label: str) -> dict[str, Any]:
    framework_id = framework["id"]
    comp_id = component_id(framework_id, label)
    seed = COMPONENT_SEEDS.get(framework_id, {}).get(comp_id)
    if seed:
        return {
            "id": comp_id,
            "label": label,
            "description": seed["description"],
            "prompt": seed["prompt"],
            "questions": seed["questions"],
        }
    return generic_component(framework, label, comp_id)


def enrich_catalog(catalog: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for framework in catalog:
        item = dict(framework)
        labels = parse_labels(framework)
        components = [build_component(framework, label) for label in labels]
        # Stable key order inside each component object.
        item["components"] = [
            {
                "id": component["id"],
                "label": component["label"],
                "description": component["description"],
                "prompt": component["prompt"],
                "questions": component["questions"],
            }
            for component in components
        ]
        enriched.append(item)
    return enriched


def main() -> None:
    with CATALOG_PATH.open("r", encoding="utf-8") as handle:
        catalog = json.load(handle)

    enriched = enrich_catalog(catalog)

    with CATALOG_PATH.open("w", encoding="utf-8") as handle:
        json.dump(enriched, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    component_count = sum(len(item["components"]) for item in enriched)
    print(f"Updated {len(enriched)} frameworks with {component_count} components.")


if __name__ == "__main__":
    main()
