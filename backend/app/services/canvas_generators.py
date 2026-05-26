from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .frameworks import get_framework


def _topic(goal: str) -> str:
    cleaned = re.sub(r"\s+", " ", goal.strip())
    return cleaned[:140].rstrip(".")


def _compact(value: str, limit: int = 230) -> str:
    cleaned = re.sub(r"\s+", " ", value.strip(" -|"))
    if len(cleaned) <= limit:
        return cleaned
    truncated = cleaned[: limit - 1].rstrip()
    if " " in truncated:
        truncated = truncated.rsplit(" ", 1)[0]
    return truncated.rstrip(" ,.;") + "."


@dataclass(frozen=True)
class DomainBrief:
    subject: str
    domain: str
    users: str
    workflow: str
    value_hypothesis: str
    constraints: str
    proof_metrics: list[str]
    evidence_prompts: list[str]
    adoption_risks: list[str]


def domain_brief_from_mapping(data: dict[str, Any] | None, goal: str) -> DomainBrief:
    fallback = extract_domain_brief(goal)
    if not isinstance(data, dict):
        return fallback

    def text_field(name: str, default: str) -> str:
        value = data.get(name)
        if not isinstance(value, str) or not value.strip():
            return default
        return _compact(value, 700)

    def list_field(name: str, default: list[str], limit: int = 5) -> list[str]:
        value = data.get(name)
        if not isinstance(value, list):
            return default
        cleaned = [_compact(str(item), 220) for item in value if str(item).strip()]
        return cleaned[:limit] or default

    return complete_domain_brief(DomainBrief(
        subject=text_field("subject", fallback.subject),
        domain=text_field("domain", fallback.domain),
        users=text_field("users", fallback.users),
        workflow=text_field("workflow", fallback.workflow),
        value_hypothesis=text_field("value_hypothesis", fallback.value_hypothesis),
        constraints=text_field("constraints", fallback.constraints),
        proof_metrics=list_field("proof_metrics", fallback.proof_metrics),
        evidence_prompts=list_field("evidence_prompts", fallback.evidence_prompts),
        adoption_risks=list_field("adoption_risks", fallback.adoption_risks),
    ), goal)


def complete_domain_brief(brief: DomainBrief | None, goal: str) -> DomainBrief:
    fallback = extract_domain_brief(goal)
    if brief is None:
        return fallback

    def padded(items: list[str], defaults: list[str], count: int = 5) -> list[str]:
        cleaned = [_compact(str(item), 260) for item in (items or []) if str(item).strip()]
        for item in defaults:
            if item not in cleaned:
                cleaned.append(item)
        return cleaned[:count]

    return DomainBrief(
        subject=brief.subject or fallback.subject,
        domain=brief.domain or fallback.domain,
        users=brief.users or fallback.users,
        workflow=brief.workflow or fallback.workflow,
        value_hypothesis=brief.value_hypothesis or fallback.value_hypothesis,
        constraints=brief.constraints or fallback.constraints,
        proof_metrics=padded(brief.proof_metrics, fallback.proof_metrics),
        evidence_prompts=padded(brief.evidence_prompts, fallback.evidence_prompts),
        adoption_risks=padded(brief.adoption_risks, fallback.adoption_risks),
    )


def extract_domain_brief(goal: str) -> DomainBrief:
    topic = _topic(goal)
    text = goal.lower()
    if any(term in text for term in ["algorithm", "ai", "model", "software", "saas", "commercialize", "monetize"]):
        return DomainBrief(
            subject=topic,
            domain=f"the product, technical, and market domain implied by '{topic}'",
            users="the specific buyers, operators, users, and stakeholders implied by the prompt",
            workflow=f"turn the algorithm behind '{topic}' into a repeatable product workflow with input data, user-visible output, validation evidence, and a credible sales motion",
            value_hypothesis="customers will pay if the algorithm creates a measurable advantage over their current manual, spreadsheet, vendor, or internal workflow",
            constraints="proof quality, integration effort, data access, user trust, switching costs, privacy/IP concerns, and the gap between technical performance and buyer willingness to pay",
            proof_metrics=[
                "measured improvement over the current workflow",
                "pilot conversion from qualified users",
                "time saved per completed job",
                "willingness-to-pay from target buyers",
                "repeat usage after first result",
            ],
            evidence_prompts=[
                "Find the current workaround users tolerate today.",
                "Run a concierge pilot where the algorithm result is manually reviewed before delivery.",
                "Ask target buyers what evidence they need before using the output in production.",
                "Compare performance against the most credible incumbent or manual process.",
            ],
            adoption_risks=[
                "The algorithm may be technically impressive but not packaged around a painful enough buying moment.",
                "Users may not trust recommendations unless they can inspect inputs, assumptions, and failure modes.",
                "Integration and change-management cost may exceed the perceived gain.",
            ],
        )

    return DomainBrief(
        subject=topic,
        domain=f"the domain implied by '{topic}'",
        users="the stakeholders most affected by the requested decision or initiative",
        workflow=f"convert '{topic}' into a concrete decision, experiment, metric, or execution path",
        value_hypothesis="the work is valuable if it changes a real decision, reduces uncertainty, or makes the next action clearer",
        constraints="unclear ownership, missing evidence, stakeholder disagreement, weak metrics, and premature scope expansion",
        proof_metrics=[
            "decision confidence delta",
            "evidence gathered per week",
            "assumptions resolved",
            "time to next concrete action",
        ],
        evidence_prompts=[
            "Name the strongest evidence that would confirm the direction.",
            "Name the strongest evidence that would make the team reverse course.",
            "Identify the stakeholder whose behavior matters most.",
        ],
        adoption_risks=[
            "The analysis may stay too abstract unless converted into evidence and action.",
            "The wrong stakeholder signal may dominate the decision.",
            "The team may optimize for a comfortable plan rather than a true constraint.",
        ],
    )


def _panel(
    title: str,
    prompt: str,
    options: list[str],
    value: str = "",
    option_sets: list[list[str]] | None = None,
    kind: str | None = None,
) -> dict[str, Any]:
    return {
        "title": title,
        "prompt": prompt,
        "options": options,
        "value": value,
        "option_sets": option_sets or [],
        "kind": kind or _panel_kind(title, prompt),
    }


def _panel_kind(title: str, prompt: str = "") -> str:
    text = f"{title} {prompt}".lower()
    if any(word in text for word in ["evidence", "proof", "verify", "validate", "reach"]):
        return "evidence"
    if any(word in text for word in ["metric", "signal", "measure", "acceptance", "score"]):
        return "metric"
    if any(word in text for word in ["risk", "failure", "threat", "obstacle"]):
        return "risk"
    if any(word in text for word in ["prototype", "experiment", "mvp", "test"]):
        return "experiment"
    if any(word in text for word in ["contradiction"]):
        return "contradiction"
    if any(word in text for word in ["feature", "definition", "requirement"]):
        return "definition"
    return "action"


def _panel_option_sets(kind: str, subject: str, seed_options: list[str] | None = None, metric: str = "") -> list[list[str]]:
    subject = _compact(subject, 220)
    seeds = [_compact(option, 340) for option in (seed_options or []) if option]
    templates = {
        "evidence": [
            [
                f"Collect one direct observation that confirms or weakens: {subject}.",
                "Ask three relevant people for examples, not opinions.",
                "Compare the claim against one past pattern or existing data point.",
            ],
            [
                "Name what evidence would change your mind.",
                "Look for one disconfirming case before treating the insight as true.",
                "Separate firsthand evidence from assumptions, preferences, or hearsay.",
            ],
        ],
        "action": [
            [
                f"Turn this into one reversible next move tied to: {subject}.",
                "Set a clear owner, date, and smallest visible output.",
                "Choose the lowest-drama step that creates new information quickly.",
            ],
            [
                "Convert the insight into a short conversation, prototype, or decision memo.",
                "Decide what to stop doing while this action is tested.",
                "Write the trigger that tells you to continue, revise, or abandon the move.",
            ],
        ],
        "metric": [
            [
                metric or f"Observable change connected to: {subject}.",
                "Decision confidence before versus after the next action.",
                "Number of concrete signals collected, reviewed, and acted on.",
            ],
            [
                "A pass/fail threshold written before the next experiment starts.",
                "Frequency of the desired behavior or outcome over the next review window.",
                "Time from insight to decision-ready evidence.",
            ],
        ],
        "risk": [
            [
                f"The plan may fail if the core assumption behind '{subject}' is false.",
                "The next action could produce noise instead of decision-grade evidence.",
                "The work may reduce one risk while quietly increasing another.",
            ],
            [
                "A short-term improvement could hide a deeper incompatibility or constraint.",
                "The process may become performative if no decision threshold is set.",
                "The wrong stakeholder or signal could dominate the conclusion.",
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
                "Record what would count as a pass, a partial pass, and a clear fail.",
                "Keep the experiment narrow enough that one result actually means something.",
            ],
        ],
        "contradiction": [
            [
                f"I want to improve the desired outcome in '{subject}' without worsening the most important constraint.",
                "Name the property that must improve and the property that cannot be sacrificed.",
                "Rewrite the conflict as a single sentence with both sides visible.",
            ],
            [
                "Separate the visible symptom from the underlying tradeoff.",
                "State what gets better, what gets worse, and why the current approach couples them.",
                "Define the contradiction so a prototype can test it rather than debate it.",
            ],
        ],
        "definition": [
            [
                f"Rewrite '{subject}' as a concrete requirement with user, trigger, behavior, and outcome.",
                "Cut any wording that does not change the build, decision, or test.",
                "Name the smallest version that still proves the core value.",
            ],
            [
                "Describe who uses it, what they do, and how success is visible.",
                "Separate the required behavior from polish, automation, or nice-to-have surface area.",
                "Add one explicit non-goal so scope does not expand silently.",
            ],
        ],
    }
    option_sets = templates.get(kind, templates["action"])
    if len(seeds) >= 3:
        option_sets = [seeds[:3], *option_sets]
    return option_sets


def _swot_item(text: str, rationale: str, options: list[str], metric: str) -> dict[str, Any]:
    return {
        "text": _compact(text, 260),
        "rationale": _compact(rationale, 320),
        "metric": _compact(metric, 180),
        "options": [_compact(option, 340) for option in options],
        "drilldown": {
            "description": "Convert this strategic observation into evidence, decisions, and execution checks.",
            "panels": [
                _panel(
                    "Evidence to verify",
                    "Pick or edit the strongest proof that should support this claim.",
                    options[:2] + [f"Interview 5 relevant users or stakeholders about: {text}"],
                    value=options[0] if options else "",
                    option_sets=_panel_option_sets("evidence", text, options),
                    kind="evidence",
                ),
                _panel(
                    "Strategic action",
                    "Choose the move this insight should trigger next.",
                    [
                        f"Turn this into a 7-day validation sprint: {text}",
                        "Assign one owner, one decision deadline, and one measurable output.",
                        "Defer this until the highest-risk assumption has evidence.",
                    ],
                    option_sets=_panel_option_sets("action", text),
                    kind="action",
                ),
                _panel(
                    "Watch metric",
                    "Select the metric that should prove this insight mattered.",
                    [item for item in [metric, "Evidence collected per week", "Decision confidence delta after validation"] if item],
                    option_sets=_panel_option_sets("metric", text, metric=metric),
                    kind="metric",
                ),
            ],
        },
    }


def generate_swot(goal: str, domain_brief: DomainBrief | None = None) -> dict[str, Any]:
    brief = complete_domain_brief(domain_brief, goal)
    topic = brief.subject

    return {
        "type": "quadrant",
        "title": f"{_compact(topic.title(), 70)} SWOT",
        "subtitle": f"Domain-specific audit for: {_topic(goal)}",
        "analysis_brief": [
            f"OmniFrame read the request as {brief.domain}. The likely users are {brief.users}.",
            f"The core workflow is to {brief.workflow}.",
            f"The value hypothesis: {brief.value_hypothesis}.",
            f"Critical constraints: {brief.constraints}.",
        ],
        "sections": [
            {
                "id": "strengths",
                "component_id": "strengths",
                "label": "Strengths",
                "prompt": "Internal advantages to preserve or amplify.",
                "items": [
                    _swot_item(
                        f"The central asset is the algorithmic know-how behind {topic}, not just a generic product idea.",
                        f"If the algorithm can produce a measurable outcome in the target workflow, it can become a credible wedge for {brief.users}.",
                        [
                            f"Show one before/after example using a real or realistic input from the workflow: {brief.workflow}.",
                            f"Translate the algorithm output into buyer language: {brief.value_hypothesis}.",
                            "Identify what is proprietary: optimization logic, benchmark data, integration layer, or workflow UX.",
                        ],
                        brief.proof_metrics[0],
                    ),
                    _swot_item(
                        f"A focused pilot with {brief.users} can turn technical performance into market credibility.",
                        "Early commercialization depends on proof that the result is safe, explainable, and worth switching behavior for.",
                        [
                            brief.evidence_prompts[0],
                            brief.evidence_prompts[1],
                            "Convert the first pilot into a report with baseline, optimized result, risk check, and ROI.",
                        ],
                        "qualified pilot conversion rate",
                    ),
                    _swot_item(
                        "The product can be positioned around decision-grade evidence rather than broad claims.",
                        "A narrow, well-instrumented proof is more persuasive than a vague promise that the algorithm is better.",
                        [
                            brief.evidence_prompts[2],
                            "Document false positives, unsafe cases, and situations where the algorithm should refuse to optimize.",
                            "Make the first demo show the original input, the optimized output, and why the change is safe.",
                        ],
                        "credible benchmark examples completed",
                    ),
                ],
            },
            {
                "id": "weaknesses",
                "component_id": "weaknesses",
                "label": "Weaknesses",
                "prompt": "Internal limitations that could slow execution.",
                "items": [
                    _swot_item(
                        f"Commercializing {topic} requires trust, integration, and validation, not only algorithm performance.",
                        brief.constraints,
                        [
                            "List the cases where the algorithm is allowed to act automatically versus cases requiring human review.",
                            "Name the integration or data format that must work first for a credible pilot.",
                            "Define what evidence is required before users rely on the output in production.",
                        ],
                        "blocked production assumptions resolved",
                    ),
                    _swot_item(
                        "The buyer may not pay for optimization unless the result maps directly to money, time, or risk reduction.",
                        "A technical win is not enough if users cannot see ROI, trust the recommendation, or fit it into their existing workflow.",
                        [
                            f"Ask {brief.users} what they would need to see before paying.",
                            f"Measure {brief.proof_metrics[0]} and {brief.proof_metrics[1]} on the same pilot artifact.",
                            "Price the first offer around verified savings or avoided cost, not feature count.",
                        ],
                        "willingness-to-pay after proof",
                    ),
                    _swot_item(
                        "The first release could fail if the product cannot handle edge cases safely.",
                        brief.adoption_risks[0],
                        [
                            "Create a failure taxonomy before pilots: unsafe output, incompatible input, weak ROI, and unclear recommendation.",
                            "Add a manual review fallback so early users never receive an untrusted result as final.",
                            "Log every rejected or low-confidence case as product learning.",
                        ],
                        "unsafe or low-confidence case rate",
                    ),
                ],
            },
            {
                "id": "opportunities",
                "component_id": "opportunities",
                "label": "Opportunities",
                "prompt": "External openings worth exploiting.",
                "items": [
                    _swot_item(
                        f"{brief.users} may have urgent cost pressure if the workflow consumes expensive labor, machine time, or expert review.",
                        f"The opportunity is strongest where {brief.value_hypothesis}.",
                        [
                            "Find the buyer segment with the clearest money leak, delay, or quality risk.",
                            f"Use this proof metric as the headline claim: {brief.proof_metrics[0]}.",
                            "Build the first case study around one painful recurring job, not a universal platform story.",
                        ],
                        "urgent workflow pain interviews completed",
                    ),
                    _swot_item(
                        "Distribution can start through trusted workflow surfaces and expert communities instead of generic SaaS ads.",
                        "Commercialization is easier when the product enters where users already inspect, edit, quote, or validate work.",
                        [
                            "Identify software, consultants, equipment vendors, forums, or service bureaus already trusted by the target users.",
                            "Offer a partner-visible benchmark report they can share with prospects.",
                            "Turn pilot outcomes into a reusable ROI calculator.",
                        ],
                        "partner-referred pilot starts",
                    ),
                    _swot_item(
                        "A narrow wedge can beat broad incumbents if it solves one high-value workflow deeply.",
                        "The first offer should be specific enough that users recognize their exact problem in the demo.",
                        [
                            f"Choose one user segment from: {brief.users}.",
                            "Remove anything not needed for one repeatable paid pilot.",
                            f"Frame the first demo around {brief.workflow}.",
                        ],
                        "segment-specific pilot success",
                    ),
                ],
            },
            {
                "id": "threats",
                "component_id": "threats",
                "label": "Threats",
                "prompt": "External forces that could reduce odds of success.",
                "items": [
                    _swot_item(
                        "Existing tools, manual expert review, and incumbent software may be 'good enough' substitutes.",
                        brief.adoption_risks[1] if len(brief.adoption_risks) > 1 else "Substitutes matter when they already own trust, workflow access, or procurement.",
                        [
                            "Name the current substitute and what users trust about it.",
                            f"Prove the algorithm wins on at least one metric: {', '.join(brief.proof_metrics[:3])}.",
                            "Test whether users switch behavior, not just whether they compliment the concept.",
                        ],
                        "substitute-to-product switch rate",
                    ),
                    _swot_item(
                        "Security, IP, liability, and integration concerns can block adoption even when the math works.",
                        brief.adoption_risks[2] if len(brief.adoption_risks) > 2 else brief.constraints,
                        [
                            "Decide whether the first pilot must support anonymized files, on-prem processing, or strict data deletion.",
                            "Add an explainability layer that shows what changed and why.",
                            "Create a fallback path where the product recommends changes without rewriting production files.",
                        ],
                        "security and integration blockers resolved",
                    ),
                    _swot_item(
                        "The market window can close if pilots do not quickly prove value in the real workflow.",
                        "The first version should create a credible evidence package before competitors, incumbents, or internal tools absorb the opportunity.",
                        [
                            f"Define what must be learned in 30 days about {brief.workflow}.",
                            "Cut any feature that does not create proof for buying, trusting, or integrating the output.",
                            "Use the report export as a decision artifact for pilot buyers and stakeholders.",
                        ],
                        "30-day evidence package completeness",
                    ),
                ],
            },
        ],
    }


def _rice_score(row: dict[str, Any]) -> float:
    return round(row["reach"] * row["impact"] * (row["confidence"] / 100) / row["effort"], 1)


def _rice_row(
    initiative: str,
    reach: int,
    impact: int,
    confidence: int,
    effort: int,
    rationale: str,
    options: list[str],
    evidence: list[str],
) -> dict[str, Any]:
    row = {
        "initiative": _compact(initiative, 120),
        "reach": reach,
        "impact": impact,
        "confidence": confidence,
        "effort": effort,
        "rationale": _compact(rationale, 340),
        "options": [_compact(option, 340) for option in options],
        "evidence": [_compact(item, 340) for item in evidence],
    }
    row["score"] = _rice_score(row)
    row["drilldown"] = {
        "description": "Interrogate the score before committing build time.",
        "panels": [
            _panel(
                "Feature definition",
                "Use a generated feature slice or edit it into a tighter requirement.",
                options,
                value=options[0] if options else initiative,
                option_sets=_panel_option_sets("definition", initiative, options),
                kind="definition",
            ),
            _panel(
                "Reach evidence",
                "Choose what should justify the reach estimate.",
                evidence,
                value=evidence[0] if evidence else "",
                option_sets=_panel_option_sets("evidence", initiative, evidence),
                kind="evidence",
            ),
            _panel(
                "Risk reducer",
                "Pick a way to increase confidence or reduce effort.",
                [
                    "Ship a concierge/manual version before automating the full workflow.",
                    "Instrument the first user action that proves demand.",
                    "Cut nonessential UI until the scoring assumption is validated.",
                ],
                option_sets=_panel_option_sets("risk", initiative),
                kind="risk",
            ),
            _panel(
                "Acceptance signal",
                "Define what makes this initiative complete enough for the next planning pass.",
                [
                    f"Score improves because confidence rises above {min(confidence + 10, 95)}% without increasing effort.",
                    "Users complete the core task without a support prompt.",
                    "The exported report explains the decision well enough for stakeholders.",
                ],
                option_sets=_panel_option_sets("metric", initiative, metric=f"Score improves because confidence rises above {min(confidence + 10, 95)}%"),
                kind="metric",
            ),
        ],
    }
    return row


def generate_rice(goal: str, domain_brief: DomainBrief | None = None) -> dict[str, Any]:
    brief = complete_domain_brief(domain_brief, goal)
    topic = brief.subject

    rows = [
        _rice_row(
            f"Benchmark the core {topic} result against the current workflow",
            800,
            5,
            76,
            3,
            f"The fastest route to credibility is proving that {brief.value_hypothesis}.",
            [
                brief.evidence_prompts[0],
                f"Produce a before/after result using the workflow: {brief.workflow}.",
                "Package the result as a pilot report with baseline, optimized output, confidence, and caveats.",
            ],
            [
                f"Reach is high because every commercialization path depends on proof for {brief.users}.",
                f"Impact is high if the benchmark moves {brief.proof_metrics[0]}.",
                "Confidence is moderate until real-world examples and edge cases are tested.",
            ],
        ),
        _rice_row(
            "Create a narrow pilot workflow for the best early buyer segment",
            500,
            4,
            70,
            4,
            f"A focused prototype creates better evidence than a broad platform because the users are specific: {brief.users}.",
            [
                f"Choose one segment from {brief.users} and one painful job from the workflow.",
                "Run the pilot with human review before automation makes production-impacting changes.",
                "Capture objection, trust, integration, and willingness-to-pay signals.",
            ],
            [
                "Reach is narrower because the first segment is intentionally focused.",
                "Impact is high because it creates adoption evidence instead of only technical proof.",
                "Confidence is moderate until user testing starts.",
            ],
        ),
        _rice_row(
            "Instrument safety, ROI, and adoption metrics from the first run",
            1000,
            4,
            84,
            2,
            "Measurement should ship with the prototype so the team can prove business value and avoid unsafe recommendations.",
            [
                f"Track {', '.join(brief.proof_metrics[:3])}.",
                "Log every rejected, low-confidence, or manually corrected output.",
                "Capture whether the pilot buyer would use, pay, or refer after seeing the result.",
            ],
            [
                "Reach touches every pilot and later every production run.",
                "Impact is high because it decides whether commercialization is credible.",
                "Confidence is high because instrumentation can be added before scaling.",
            ],
        ),
    ]

    rows = sorted(rows, key=lambda row: row["score"], reverse=True)

    return {
        "type": "score_table",
        "title": "RICE Prioritization Canvas",
        "subtitle": f"Inferred feature ranking for: {_topic(goal)}",
        "formula": "Reach x Impact x Confidence / Effort",
        "analysis_brief": [
            f"OmniFrame inferred {len(rows)} buildable initiatives for {brief.domain}.",
            f"Scores favor proof for {brief.users}, especially {', '.join(brief.proof_metrics[:3])}.",
            "Click any initiative to open a focused workspace with generated options you can accept, combine, or edit. Export a PDF when the analysis is ready to share.",
        ],
        "rows": rows,
    }


@dataclass(frozen=True)
class TrizPrinciple:
    number: int
    name: str
    application: str
    why_it_fits: str = ""
    panels: list[dict[str, Any]] | None = None


TRIZ_STARTERS = [
    TrizPrinciple(1, "Segmentation", "Break the system into independent modules so each constraint can be optimized separately."),
    TrizPrinciple(10, "Preliminary action", "Move expensive or slow preparation before the critical moment."),
    TrizPrinciple(15, "Dynamics", "Let structure, policy, or configuration adapt as conditions change."),
    TrizPrinciple(24, "Intermediary", "Introduce a buffer, broker, adapter, or translation layer between conflicting needs."),
    TrizPrinciple(35, "Parameter change", "Change density, timing, temperature, precision, or another key parameter instead of forcing the same design."),
]


def _triz_principle_dict(principle: TrizPrinciple) -> dict[str, Any]:
    return {
        "number": principle.number,
        "name": principle.name,
        "application": principle.application,
        "why_it_fits": principle.why_it_fits,
        "drilldown": {
            "description": principle.application,
            "panels": principle.panels or [],
        },
    }


def generate_triz(goal: str, domain_brief: DomainBrief | None = None) -> dict[str, Any]:
    brief = complete_domain_brief(domain_brief, goal)
    topic = brief.subject
    contradiction = {
        "improving": f"Improve the desired outcome for {topic}: {brief.value_hypothesis}",
        "worsening": f"Protect against the main constraints and side effects: {brief.constraints}",
        "prompt": f"Rewrite these two fields into a domain-specific contradiction for {topic} before selecting a principle.",
    }
    analysis_brief = [
        f"OmniFrame read the domain as {brief.domain}.",
        f"The TRIZ contradiction should improve {brief.value_hypothesis} while protecting against {brief.constraints}.",
        f"Use the focused workspaces to translate each principle into a domain-specific move, prototype, and failure check for {brief.workflow}.",
    ]
    return {
        "type": "contradiction",
        "title": "TRIZ Contradiction Canvas",
        "subtitle": f"Inventive problem-solving for: {topic}",
        "analysis_brief": analysis_brief,
        "contradiction": contradiction,
        "principles": [_triz_principle_dict(principle) for principle in TRIZ_STARTERS],
        "solution_cards": [
            {
                "title": "Separate in time",
                "body": f"Move the expensive or risky part of {brief.workflow} before the critical user-facing moment.",
            },
            {
                "title": "Separate in structure",
                "body": f"Split the part of the system that creates value from the part that creates risk: {brief.constraints}.",
            },
            {
                "title": "Introduce a mediation layer",
                "body": f"Use review, simulation, facilitation, policy, or tooling between the raw idea and the high-stakes decision for {topic}.",
            },
        ],
    }


def _board_item(title: str, body: str, options: list[str], metric: str = "") -> dict[str, Any]:
    return {
        "title": _compact(title, 120),
        "body": _compact(body, 380),
        "metric": _compact(metric, 160),
        "options": [_compact(option, 340) for option in options],
        "drilldown": {
            "description": "Use the generated options, then edit the notes into a decision-grade output.",
            "panels": [
                _panel(
                    "Best next move",
                    "Choose or edit the next concrete move.",
                    options,
                    value=options[0] if options else "",
                    option_sets=_panel_option_sets("action", title, options),
                    kind="action",
                ),
                _panel(
                    "Evidence needed",
                    "Select the evidence that would make this recommendation credible.",
                    [
                        f"Interview target users about: {title}",
                        "Gather one concrete data point that could invalidate this assumption.",
                        "Create a before/after metric that can be exported in the report.",
                    ],
                    option_sets=_panel_option_sets("evidence", title),
                    kind="evidence",
                ),
                _panel(
                    "Decision metric",
                    "Pick the measurement that determines whether this stays in the plan.",
                    [item for item in [metric, "Decision confidence improvement", "Time-to-evidence"] if item],
                    option_sets=_panel_option_sets("metric", title, metric=metric),
                    kind="metric",
                ),
            ],
        },
    }


def generate_lean_startup(goal: str, domain_brief: DomainBrief | None = None) -> dict[str, Any]:
    brief = complete_domain_brief(domain_brief, goal)
    topic = brief.subject
    return {
        "type": "framework_board",
        "title": "Lean Startup Experiment Canvas",
        "subtitle": f"Build-Measure-Learn plan for: {_topic(goal)}",
        "analysis_brief": [
            f"OmniFrame read the request as {brief.domain}.",
            f"The key customer hypothesis is whether {brief.users} will pay because {brief.value_hypothesis}.",
            f"The experiment must prove value inside this workflow: {brief.workflow}.",
            "Hover over each card for guidance, open focused workspaces for deeper notes, and export the experiment plan as PDF.",
        ],
        "lanes": [
            {
                "id": "build",
                "label": "Build",
                "prompt": "Smallest artifact that can test the riskiest assumption.",
                "items": [
                    _board_item(
                        "Riskiest assumption",
                        f"{brief.users} have a painful enough job to try {topic} now.",
                        [
                            f"Write the assumption as: '{brief.value_hypothesis}'.",
                            f"Recruit 5 users who already work through: {brief.workflow}.",
                            brief.evidence_prompts[1],
                        ],
                        "Assumption pass/fail evidence",
                    ),
                    _board_item(
                        "MVP artifact",
                        f"Use a concierge demo or manually reviewed workflow before automating production use of {topic}.",
                        [
                            f"Build a one-screen promise around {brief.proof_metrics[0]}.",
                            "Use sample or anonymized customer inputs if production data is sensitive.",
                            "Instrument trust objections, integration blockers, and willingness to pay from day one.",
                        ],
                        "Time from contact to validated signal",
                    ),
                ],
            },
            {
                "id": "measure",
                "label": "Measure",
                "prompt": "Signals that prove behavior, not compliments.",
                "items": [
                    _board_item(
                        "Actionable metric",
                        f"Favor concrete proof such as {', '.join(brief.proof_metrics[:3])} over vanity interest.",
                        [
                            f"Define one primary metric: {brief.proof_metrics[0]}.",
                            "Log qualitative objections beside every numeric result.",
                            "Separate curiosity from actual workflow adoption.",
                        ],
                        "Validated conversion rate",
                    ),
                    _board_item(
                        "Cohort learning",
                        "Compare user segments so the team learns where the product has a wedge.",
                        [
                            f"Tag results by segment within {brief.users}, pain intensity, existing workaround, and buying authority.",
                            "Find the segment where urgency is highest and support burden is lowest.",
                            "Export a cohort summary before deciding what to build next.",
                        ],
                        "Segment-specific activation",
                    ),
                ],
            },
            {
                "id": "learn",
                "label": "Learn",
                "prompt": "Explicit pivot, persevere, or stop logic.",
                "items": [
                    _board_item(
                        "Pivot/persevere rule",
                        "Decide in advance what evidence earns more investment.",
                        [
                            f"Persevere only if target users see measurable movement in {brief.proof_metrics[0]}.",
                            "Pivot if users like the concept but keep using their old workaround.",
                            "Stop if the strongest segment will not trade time, money, or sensitive data for the result.",
                        ],
                        "Decision made by deadline",
                    )
                ],
            },
        ],
    }


def generate_okrs(goal: str, domain_brief: DomainBrief | None = None) -> dict[str, Any]:
    brief = complete_domain_brief(domain_brief, goal)
    topic = brief.subject
    return {
        "type": "okr_board",
        "title": "OKR Alignment Canvas",
        "subtitle": f"Objectives and measurable outcomes for: {_topic(goal)}",
        "analysis_brief": [
            f"OmniFrame read the request as {brief.domain}.",
            f"These OKRs turn {topic} into measurable proof for {brief.users}.",
        ],
        "objectives": [
            {
                "objective": f"Prove {topic} creates measurable workflow value",
                "rationale": "The objective is intentionally qualitative; the key results below make it measurable.",
                "key_results": [
                    f"KR1: prove {brief.proof_metrics[0]} on at least 5 representative cases.",
                    f"KR2: secure 3 qualified pilot conversations with {brief.users}.",
                    "KR3: produce one exported report that names buyer segment, owner, deadline, risks, and next experiment.",
                ],
                "items": [
                    _board_item(
                        "Owner alignment",
                        "Make one accountable owner visible for every key result.",
                        [
                            "Assign one owner for benchmark evidence and one owner for buyer discovery.",
                            "Add a weekly confidence check to the Wisdom Graph.",
                            f"Convert vague work into measurable movement in {brief.proof_metrics[0]}.",
                        ],
                        "KR owner coverage",
                    )
                ],
            },
            {
                "objective": "Turn commercialization analysis into pilot behavior",
                "rationale": "OKRs fail when they become static statements rather than a weekly operating system.",
                "key_results": [
                    f"KR1: every initiative maps to one of: {', '.join(brief.proof_metrics[:3])}.",
                    "KR2: weekly review captures progress, confidence, blocker status, and customer evidence.",
                    "KR3: at least one initiative is cut or changed based on pilot evidence.",
                ],
                "items": [
                    _board_item(
                        "Weekly operating rhythm",
                        "Use the canvas to keep the OKR alive after the initial planning session.",
                        [
                            "Review KR movement before discussing tasks.",
                            "Flag initiatives that consume effort without moving a KR.",
                            "Export an updated report after each major decision.",
                        ],
                        "KR movement per week",
                    )
                ],
            },
        ],
    }


def generate_porters_five_forces(goal: str, domain_brief: DomainBrief | None = None) -> dict[str, Any]:
    brief = complete_domain_brief(domain_brief, goal)
    topic = brief.subject
    forces = [
        (
            "Competitive rivalry",
            "How intense is direct competition, and where are incumbents vulnerable?",
            "High rivalry means the strategy needs differentiation, speed, or a niche wedge.",
        ),
        (
            "Threat of new entrants",
            "How easy is it for new players to copy the offer?",
            "Low switching costs and accessible tools raise entrant risk.",
        ),
        (
            "Threat of substitutes",
            "What workaround already solves the job well enough?",
            "Substitutes can be spreadsheets, agencies, social groups, manual workflows, or doing nothing.",
        ),
        (
            "Buyer power",
            "Can customers force lower prices, custom demands, or long sales cycles?",
            "Buyer concentration and low urgency weaken pricing power.",
        ),
        (
            "Supplier power",
            "Do platforms, data providers, model vendors, or distribution partners control critical inputs?",
            "Dependency on scarce data, APIs, or talent can compress margin.",
        ),
    ]
    return {
        "type": "force_map",
        "title": "Porter's Five Forces Canvas",
        "subtitle": f"Industry structure read for: {_topic(goal)}",
        "analysis_brief": [
            f"OmniFrame read the request as {brief.domain}.",
            f"The force map evaluates whether {brief.users} can be reached profitably despite {brief.constraints}.",
        ],
        "forces": [
            {
                "name": name,
                "intensity": intensity,
                "question": question,
                "implication": implication,
                "items": [
                    _board_item(
                        f"{name} evidence",
                        implication,
                        [
                            f"List the top three facts that make {name.lower()} high, medium, or low for {topic}.",
                            f"Name the current alternative {brief.users} would choose if this product did not exist.",
                            f"Choose one move that improves structural advantage around {brief.workflow}.",
                        ],
                        "Force confidence rating",
                    )
                ],
            }
            for (name, question, implication), intensity in zip(forces, ["High", "Medium", "High", "Medium", "Medium"], strict=True)
        ],
    }


def generate_pestle(goal: str, domain_brief: DomainBrief | None = None) -> dict[str, Any]:
    brief = complete_domain_brief(domain_brief, goal)
    topic = brief.subject
    factors = [
        ("Political", "Policy, government incentives, procurement behavior, geopolitical pressure."),
        ("Economic", "Budget cycles, inflation, purchasing power, capital availability, cost pressure."),
        ("Social", "Behavior shifts, cultural adoption, trust, demographics, user expectations."),
        ("Technological", "Platform shifts, AI capability, data access, integration maturity, security."),
        ("Legal", "Privacy, IP, employment, consumer protection, sector regulations, contract risk."),
        ("Environmental", "Sustainability, energy use, materials, logistics, climate exposure."),
    ]
    return {
        "type": "framework_board",
        "title": "PESTLE Macro Risk Canvas",
        "subtitle": f"Macro-environment scan for: {_topic(goal)}",
        "analysis_brief": [
            f"OmniFrame read the request as {brief.domain}.",
            f"Use PESTLE to track macro forces that change buyer urgency, trust, security, and integration risk for {brief.users}.",
        ],
        "lanes": [
            {
                "id": name.lower(),
                "component_id": name.lower(),
                "label": name,
                "prompt": description,
                "items": [
                    _board_item(
                        f"{name} force for {topic}",
                        description,
                        [
                            f"Name the most important {name.lower()} factor that could affect {brief.workflow}.",
                            "Classify the factor as tailwind, headwind, or watch item.",
                            f"Define the earliest signal that would tell the team to adapt for {brief.users}.",
                        ],
                        f"{name} watch signal",
                    )
                ],
            }
            for name, description in factors
        ],
    }


def _catalog_seed_options(component: dict[str, Any], topic: str) -> list[str]:
    # The component `prompt` is an LLM instruction and is never surfaced as display
    # text; seed options come from `questions`, falling back to the short description.
    questions = component.get("questions") or []
    seeds = [_compact(str(question), 340) for question in questions if str(question).strip()]
    if not seeds:
        description = component.get("description") or ""
        if str(description).strip():
            seeds = [_compact(str(description), 340)]
    return seeds[:3] or [f"Clarify how this applies to {topic}."]


def _board_from_components(components: list[dict[str, Any]], topic: str) -> list[dict[str, Any]]:
    lanes: list[dict[str, Any]] = []
    for component in components:
        label = _compact(component.get("label") or component.get("id") or "Component", 80)
        body = _compact(
            component.get("description") or f"Examine {label.lower()} for {topic}.",
            380,
        )
        component_id = component.get("id") or label.lower().replace(" ", "_")
        lanes.append(
            {
                "id": component_id,
                "component_id": component_id,
                "label": label,
                "prompt": _compact(component.get("description") or "", 200),
                # Title is the component label; body holds the per-component LLM result.
                # No canned metric — the card surfaces the generated content, not scaffolding.
                "items": [_board_item(label, body, _catalog_seed_options(component, topic))],
            }
        )
    return lanes


def _quadrant_from_components(components: list[dict[str, Any]], topic: str) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    for component in components:
        label = _compact(component.get("label") or component.get("id") or "Component", 80)
        text = _compact(
            component.get("description") or f"Examine {label.lower()} for {topic}.",
            260,
        )
        rationale = ""
        component_id = component.get("id") or label.lower().replace(" ", "_")
        sections.append(
            {
                "id": component_id,
                "component_id": component_id,
                "label": label,
                "prompt": _compact(component.get("description") or "", 200),
                "items": [
                    # No canned metric — the card surfaces the per-component LLM result (item text).
                    _swot_item(text, rationale, _catalog_seed_options(component, topic), "")
                ],
            }
        )
    return sections


def generate_from_catalog(framework_id: str, goal: str, domain_brief: DomainBrief | None = None) -> dict[str, Any]:
    """Build a canvas for any catalog framework purely from its catalog entry.

    Used as the fallback for frameworks that have no bespoke generator. The render
    shape is declared per framework via the catalog's ``canvas_type`` field.
    """
    brief = complete_domain_brief(domain_brief, goal)
    topic = brief.subject
    framework = get_framework(framework_id) or {}
    name = framework.get("name") or framework_id.replace("_", " ").title()
    components = framework.get("components") or []
    canvas_type = framework.get("canvas_type") or "framework_board"
    selection_lens = framework.get("selection_lens") or ""
    core_components = framework.get("core_components") or ""

    analysis_brief = [f"OmniFrame read the request as {brief.domain}."]
    if selection_lens:
        analysis_brief.append(f"{name} fits here: {_compact(selection_lens, 300)}")
    else:
        analysis_brief.append(f"{name} structures the analysis for {topic}.")
    if core_components:
        analysis_brief.append(f"Core components: {_compact(core_components, 240)}.")
    analysis_brief.append("Open any card for suggested evidence, actions, and metrics, then export the report.")

    base = {
        "title": f"{name} Canvas",
        "subtitle": f"Framework analysis for: {_topic(goal)}",
        "analysis_brief": analysis_brief,
    }

    # The quadrant renderer is a fixed 2x2 grid, so only use it for 4-component frameworks.
    if canvas_type == "quadrant" and len(components) == 4:
        return {**base, "type": "quadrant", "sections": _quadrant_from_components(components, topic)}

    # framework_board wraps any number of lanes and is the safe default for every other
    # case: framework_board frameworks, quadrant frameworks whose component count does not
    # fit the 2x2 grid, and declared okr_board/force_map/score_table/contradiction
    # frameworks that lack a bespoke generator.
    lanes = _board_from_components(components, topic)
    if not lanes:
        lanes = [
            {
                "id": "analysis",
                "label": name,
                "prompt": _compact(selection_lens, 200),
                "items": [
                    _board_item(
                        f"Apply {name} to {_compact(topic, 60)}",
                        brief.value_hypothesis,
                        brief.evidence_prompts[:3],
                        brief.proof_metrics[0],
                    )
                ],
            }
        ]
    return {**base, "type": "framework_board", "lanes": lanes}


GENERATORS = {
    "swot": generate_swot,
    "lean_startup": generate_lean_startup,
    "okrs": generate_okrs,
    "porters_five_forces": generate_porters_five_forces,
    "pestle": generate_pestle,
    "rice": generate_rice,
    "triz": generate_triz,
}


def build_canvas(framework_id: str, goal: str, domain_brief: DomainBrief | None = None) -> dict[str, Any]:
    generator = GENERATORS.get(framework_id)
    if generator is not None:
        return generator(goal, domain_brief)
    return generate_from_catalog(framework_id, goal, domain_brief)
