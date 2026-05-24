from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


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


def _split_sentences(value: str, limit: int = 2) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", _compact(value, 900))
    return " ".join(sentence for sentence in sentences[:limit] if sentence)


@dataclass(frozen=True)
class ParsedProject:
    rank: int | None
    name: str
    purpose: str = ""
    details: str = ""
    challenges: str = ""
    benefit: str = ""
    market: str = ""
    competitors: str = ""

    @property
    def context(self) -> str:
        return _compact(" ".join([self.purpose, self.details, self.challenges, self.benefit]), 420)


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


def extract_domain_brief(goal: str) -> DomainBrief:
    topic = _topic(goal)
    text = goal.lower()

    if any(term in text for term in ["cnc", "g-code", "gcode", "cam ", "cam/", "toolpath", "machining", "machine shop"]):
        return DomainBrief(
            subject="commercializing a CNC/CAM file optimization algorithm",
            domain="CNC machining, CAM programming, G-code/toolpath optimization, and manufacturing software commercialization",
            users="CNC job shops, machinists, CAM programmers, manufacturing engineers, quoting teams, and factory owners who pay for spindle utilization",
            workflow="analyze an existing CAM/G-code/CNC file, detect inefficient feeds, speeds, tool changes, air cuts, path order, and machine-specific constraints, then produce a safer optimized file or recommendations that can be simulated before machining",
            value_hypothesis="customers will pay if the algorithm reliably reduces cycle time, scrap risk, tool wear, quoting uncertainty, or programming time without causing machine crashes or surface-finish defects",
            constraints="trust in modified toolpaths, controller/post-processor compatibility, liability for crashes or scrapped parts, IP security for customer files, machinist skepticism, and proof that optimization works across materials, machines, and part geometries",
            proof_metrics=[
                "cycle-time reduction versus baseline CAM/G-code",
                "successful simulation or dry-run pass rate",
                "tool-wear or tooling-cost reduction",
                "scrap/rework rate after optimized file use",
                "machine-hour ROI per job",
            ],
            evidence_prompts=[
                "Benchmark 20 anonymized CNC jobs across aluminum, steel, plastics, and complex 3-axis/5-axis geometries.",
                "Ask CAM programmers which optimizations they trust enough to run on a real machine.",
                "Compare output against Fusion, Mastercam, Siemens NX, and manual machinist edits where available.",
                "Run optimized files through simulation/backplotting before any live cut.",
            ],
            adoption_risks=[
                "A single bad toolpath can break trust faster than many small cycle-time wins can build it.",
                "CAM vendors and controller ecosystems may already own distribution and integration points.",
                "Customers may refuse to upload proprietary part files without strong security and on-prem options.",
            ],
        )

    if any(term in text for term in ["algorithm", "ai", "model", "software", "saas", "commercialize", "monetize"]):
        return DomainBrief(
            subject=topic,
            domain="software commercialization and algorithm-to-product translation",
            users="technical buyers, operators, product teams, and early adopters with a painful workflow the algorithm can improve",
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
        domain="strategy and execution planning",
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


def _extract_projects(goal: str) -> list[ParsedProject]:
    matches = list(re.finditer(r"(?m)(?:^|\n)\s*(\d+)\.\s+", goal))
    projects: list[ParsedProject] = []

    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(goal)
        raw = goal[start:end].strip()
        rank_match = re.match(r"(\d+)\.\s+(.*)", raw, flags=re.S)
        if not rank_match:
            continue

        rank = int(rank_match.group(1))
        body = rank_match.group(2).strip()
        parts = [part.strip() for part in re.split(r"\t+", body) if part.strip()]
        if len(parts) < 3:
            parts = [part.strip() for part in re.split(r"\s{2,}|\s+\|\s+", body) if part.strip()]

        if len(parts) >= 3:
            projects.append(
                ParsedProject(
                    rank=rank,
                    name=_compact(parts[0], 80),
                    purpose=_compact(parts[1], 140),
                    details=_split_sentences(parts[2], 2),
                    challenges=_split_sentences(parts[3], 2) if len(parts) > 3 else "",
                    benefit=_split_sentences(parts[4], 2) if len(parts) > 4 else "",
                    market=_split_sentences(parts[5], 1) if len(parts) > 5 else "",
                    competitors=_split_sentences(parts[6], 1) if len(parts) > 6 else "",
                )
            )
        else:
            first_line = _compact(body.splitlines()[0] if body.splitlines() else body, 120)
            remainder = _compact(body.replace(first_line, "", 1), 420)
            projects.append(ParsedProject(rank=rank, name=first_line, details=remainder))

    if projects:
        return projects

    named = re.search(r"(Triangle Gig & Event Agent|Agent-Trust Cert|VeriBot|VibeOS|SprintZero|AutoValidate|Nexus)", goal, flags=re.I)
    if named:
        return [ParsedProject(rank=None, name=_compact(named.group(1), 90), details=_compact(goal, 520))]

    return []


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
                    [
                        metric,
                        "Evidence collected per week",
                        "Decision confidence delta after validation",
                    ],
                    option_sets=_panel_option_sets("metric", text, metric=metric),
                    kind="metric",
                ),
            ],
        },
    }


RELATIONSHIP_WORDS = {
    "partner",
    "breakup",
    "girlfriend",
    "boyfriend",
    "wife",
    "husband",
    "relationship",
    "dating",
    "hollie",
    "family",
    "couple",
}


def _is_relationship_goal(goal: str) -> bool:
    tokens = set(re.findall(r"[a-zA-Z][a-zA-Z-]+", goal.lower()))
    return bool(tokens & RELATIONSHIP_WORDS)


def _relationship_name(goal: str) -> str:
    named_partner = re.search(r"(?:partner|girlfriend|boyfriend|wife|husband|with her|with him)\s*\(([^),]{2,40})\)", goal, flags=re.I)
    if named_partner:
        return _compact(named_partner.group(1), 40)
    for candidate in ["Hollie"]:
        if re.search(rf"\b{re.escape(candidate)}\b", goal, flags=re.I):
            return candidate
    explicit = re.search(r"\(([^)]{2,40})\)", goal)
    if explicit:
        value = explicit.group(1)
        if "," not in value and len(value.split()) <= 3:
            return _compact(value, 40)
    return "the other person"


def _relationship_swot(goal: str, topic: str) -> dict[str, Any]:
    person = _relationship_name(goal)
    dating = "girlfriend" in goal.lower() and "breakup" not in goal.lower()
    if dating:
        strengths = [
            _swot_item(
                "You are asking for a relationship deliberately rather than passively waiting for one.",
                "That means the first useful move is to define the kind of partnership you want and the behaviors you are willing to practice.",
                [
                    "Write a partner profile based on values, daily lifestyle, conflict style, family goals, and curiosity rather than only attraction.",
                    "Ask two trusted friends which settings make you seem most relaxed, generous, and socially open.",
                    "Choose one repeatable weekly environment where compatible people are likely to be present.",
                ],
                "Weekly high-quality conversations",
            ),
            _swot_item(
                "Your interests can become natural connection points if you turn them into shared experiences.",
                "Reading, writing, music history, travel, building, and learning are relationship assets when presented as invitations rather than tests.",
                [
                    "Plan low-pressure dates around music, books, language nights, museums, hikes, or travel talks.",
                    "Practice asking about her world before explaining your own projects.",
                    "Look for mutual curiosity, not just admiration for your interests.",
                ],
                "Second-date acceptance rate",
            ),
        ]
        weaknesses = [
            _swot_item(
                "A vague desire to find a girlfriend can create mismatched dating choices.",
                "Without a clear relationship standard, loneliness can select for availability instead of compatibility.",
                [
                    "List non-negotiables, preferences, and flexible areas before dating heavily.",
                    "Define what emotional availability looks like in behavior.",
                    "Name the patterns you do not want to repeat from past relationships.",
                ],
                "Dating criteria clarity",
            )
        ]
        opportunities = [
            _swot_item(
                "The best dating strategy is repeated exposure in communities that match your real life.",
                "Compatibility is easier to notice when the environment already filters for shared values or energy.",
                [
                    "Join one recurring in-person community for travel, language, arts, volunteering, sports, or intellectual events.",
                    "Use dating apps only as one channel, with prompts that reveal values and lifestyle.",
                    "Ask for warm introductions where friends understand your desired partnership.",
                ],
                "Compatible introductions per month",
            )
        ]
        threats = [
            _swot_item(
                "Trying to perform for approval can attract the wrong match.",
                "The risk is optimizing for being chosen instead of discovering whether the relationship is actually good for both people.",
                [
                    "End conversations politely when values, availability, or kindness are clearly absent.",
                    "Do not over-invest before mutual effort is visible.",
                    "Watch whether communication feels safe, reciprocal, and curious.",
                ],
                "Reciprocity signal",
            )
        ]
    else:
        strengths = [
            _swot_item(
                f"You have named concrete needs: learning, creating, traveling, family possibility, time with Antuan, and deeper shared experiences with {person}.",
                "Specific needs are more useful than a general feeling of unhappiness because they can be discussed, tested, and negotiated.",
                [
                    f"Ask {person} for a calm conversation where each of you names three needs, three boundaries, and one repair attempt.",
                    "Separate core values from solvable logistics such as travel planning, TV time, home setup, and quality-time routines.",
                    "Write what a good relationship would look like in ordinary weekly behavior, not only in big life dreams.",
                ],
                "Clarity of needs and boundaries",
            ),
            _swot_item(
                "You are noticing specific disconnection patterns rather than only blaming the whole relationship.",
                "The Elvis movie example, travel differences, pet-shop/home conflict, and feeling exhausted can become evidence for a structured decision.",
                [
                    "Track three moments where connection was attempted, accepted, rejected, or shut down.",
                    "Ask whether each pattern is new, chronic, repairable, or tied to a temporary stressor.",
                    "Use specific examples without insults, sarcasm, or parent-child framing.",
                ],
                "Repair conversation quality",
            ),
        ]
        weaknesses = [
            _swot_item(
                "The current conversation style appears to escalate into shutdown, sarcasm, or hurt rather than mutual problem solving.",
                "Phrases like feeling exhausted, feeling empty, and the pet-shop exchange suggest the process may be damaging even before the decision is made.",
                [
                    "Remove contempt, teasing, or parent-child language before any serious decision talk.",
                    "Use one sentence at a time: 'I feel X when Y happens, and I need Z to know whether this can improve.'",
                    "Pause the conversation if either person starts defending, mocking, stonewalling, or flooding.",
                ],
                "Conflict de-escalation success",
            ),
            _swot_item(
                f"You may be mixing multiple decisions about {person}: compatibility, family, travel, money, daily connection, and household boundaries.",
                "A breakup decision becomes clearer when each issue is separated instead of treated as one emotional verdict.",
                [
                    "Score each issue as core value mismatch, negotiable preference, repairable habit, or immediate boundary.",
                    "Do not decide based only on one painful conversation unless safety or abuse is involved.",
                    "Define what evidence over the next 30 days would make staying or leaving more clearly right.",
                ],
                "Issue separation completeness",
            ),
        ]
        opportunities = [
            _swot_item(
                "A time-boxed repair attempt could reveal whether both people are still willing to meet in the middle.",
                "The goal is not to force staying; it is to gather better evidence before making a life-changing decision.",
                [
                    "Propose a 30-day repair sprint with one weekly check-in, one shared activity, and one household boundary conversation.",
                    "Ask whether travel dreams, family expectations, salary expectations, and home priorities can be discussed without contempt.",
                    "Consider a couples therapist or mediator if both people want repair but cannot talk safely alone.",
                ],
                "Mutual repair participation",
            ),
            _swot_item(
                "A respectful separation plan may also be an opportunity if values are truly incompatible.",
                "Sometimes the healthiest decision is not to win the argument, but to end the relationship with less damage.",
                [
                    "Write what a clean, respectful breakup would require emotionally, financially, logistically, and socially.",
                    "Identify shared responsibilities, housing, pets, and family impacts before acting impulsively.",
                    "Choose one trusted outside person who can help you stay fair and grounded.",
                ],
                "Separation readiness clarity",
            ),
        ]
        threats = [
            _swot_item(
                "A decision made while flooded, exhausted, or contemptuous may be less wise than one made after cooling down.",
                "The prompt contains real hurt, but the tone also shows escalation risk. That can distort judgment.",
                [
                    "Wait until you can describe the problem without ridicule before holding the decisive conversation.",
                    "If there is any risk of harm, coercion, or abuse, prioritize safety and outside support immediately.",
                    "Do not use the framework output as a weapon against Hollie; use it to prepare a calmer decision process.",
                ],
                "Decision made from calm state",
            ),
            _swot_item(
                "Staying without changed behavior could extend the same loneliness and resentment.",
                "Leaving impulsively could also create regret if both people would have engaged in repair with a clearer process.",
                [
                    "Define two stay conditions and two leave conditions before the next serious talk.",
                    "Ask whether both people can commit to observable behavior, not vague promises.",
                    "Review the decision with a therapist, mentor, or grounded friend before final action if possible.",
                ],
                "Stay/leave criteria met",
            ),
        ]

    return {
        "type": "quadrant",
        "title": "Relationship Decision SWOT",
        "subtitle": f"Personal decision audit for: {topic}",
        "analysis_brief": [
            "OmniFrame detected a relationship or dating decision, so it replaced business language with needs, patterns, boundaries, repair options, and risks.",
            "This canvas should not decide for you. It helps you slow the decision down, separate issues, and prepare a respectful next conversation or action.",
            "If there is abuse, coercion, or safety risk, prioritize immediate support from trusted people or local emergency resources over framework analysis.",
        ],
        "sections": [
            {"id": "strengths", "label": "Strengths", "prompt": "Resources, values, and clarity you can bring to the relationship decision.", "items": strengths},
            {"id": "weaknesses", "label": "Weaknesses", "prompt": "Patterns that may distort judgment or block repair.", "items": weaknesses},
            {"id": "opportunities", "label": "Opportunities", "prompt": "Healthy repair paths or respectful transition paths.", "items": opportunities},
            {"id": "threats", "label": "Threats", "prompt": "Risks of acting too fast, staying too long, or escalating harm.", "items": threats},
        ],
    }


def _project_specific_swot(projects: list[ParsedProject], topic: str) -> dict[str, Any]:
    names = ", ".join(project.name for project in projects[:5])
    first = projects[0]
    second = projects[1] if len(projects) > 1 else first
    third = projects[2] if len(projects) > 2 else first
    fourth = projects[3] if len(projects) > 3 else second
    fifth = projects[4] if len(projects) > 4 else third

    strengths = [
        _swot_item(
            f"{third.name} has a concrete wedge: local data curation can start in one geography before global scale is required.",
            third.details or third.context,
            [
                f"Seed {third.name} manually for one dense neighborhood, then let agents maintain freshness.",
                "Use curator QA to make the first 100 users feel the data is cleaner than social feeds.",
                "Track whether first users save, share, or revisit events within 7 days.",
            ],
            "Weekly active saved events and verified fresh listings",
        ),
        _swot_item(
            f"{fourth.name} converts idea risk into a measurable pre-build product, which is valuable while software is cheap but attention is scarce.",
            fourth.benefit or fourth.context,
            [
                f"Package {fourth.name} as a founder diagnostic report, not just a landing-page tool.",
                "Benchmark ad click, interview conversion, and waitlist quality against idea category norms.",
                "Make the output emotionally useful even when the answer is negative.",
            ],
            "Validation report completion rate and paid re-run rate",
        ),
        _swot_item(
            f"{first.name} can own an emerging trust layer if autonomous commerce protocols become merchant priorities.",
            first.details or first.context,
            [
                "Position the badge as machine-readable proof for agent buyers, not another consumer trust seal.",
                "Prototype verification checks around refundability, inventory accuracy, and fraud signals.",
                "Build one protocol demo with AP2/UCP-style procurement flows.",
            ],
            "Verified merchant pilot count and agent checkout success rate",
        ),
    ]

    weaknesses = [
        _swot_item(
            f"{second.name} combines workflow SaaS, marketplace liquidity, agreements, and code reuse, creating a very wide first release surface.",
            second.challenges or second.context,
            [
                "Reduce V1 to AI requirements interviews plus handoff artifacts before adding marketplace liquidity.",
                "Ship founder-to-vibecoder matching as concierge workflow until repeat demand is proven.",
                "Define the one workflow that must feel flawless before adding repo/package features.",
            ],
            "Time from raw idea to approved PRD",
        ),
        _swot_item(
            f"{third.name} depends on messy sources like Instagram, flyers, and stale venue pages, so freshness and deduplication are product-critical.",
            third.challenges or third.context,
            [
                "Score every event by source reliability, recency, duplicate confidence, and venue confirmation.",
                "Start with assisted scraping plus human review before promising daily full autonomy.",
                "Expose freshness badges so users understand why the feed is trustworthy.",
            ],
            "Duplicate rate, stale event rate, and verified listing coverage",
        ),
        _swot_item(
            f"{fifth.name} may face high compute cost before it has a repeatable buyer for cross-domain insight discovery.",
            fifth.challenges or fifth.context,
            [
                "Gate expensive searches behind user-paid research briefs.",
                "Cache corpus intersections and rank insights by novelty before synthesis.",
                "Start with two databases where the overlap is valuable and technically tractable.",
            ],
            "Cost per valuable insight and paid brief conversion",
        ),
    ]

    opportunities = [
        _swot_item(
            f"The portfolio spans trust infrastructure, AI-native execution, local culture, validation, and research, giving OmniFrame several distinct wedge tests.",
            topic,
            [
                f"Run a comparative RICE pass across {names} to choose one hackathon demo wedge.",
                "Use customer pain immediacy, demo feasibility, and distribution clarity as the top filters.",
                "Turn each idea into a 30-day proof plan with one buyer/user and one evidence metric.",
            ],
            "Evidence velocity per concept",
        ),
        _swot_item(
            f"{third.name} has sponsorship and ticketing paths once enough local supply and demand is curated.",
            third.market or third.benefit or third.context,
            [
                "Offer venues a sponsored placement only after organic event quality is credible.",
                "Use artist/open-mic workflows to generate supply while consumer discovery builds demand.",
                "Create weekly culture digests that venues can sponsor locally.",
            ],
            "Venue lead conversion and sponsored listing revenue",
        ),
        _swot_item(
            f"{fourth.name} and {second.name} can reinforce each other: validated ideas can flow into requirements workshops and implementation teams.",
            f"{fourth.context} {second.context}",
            [
                "Make AutoValidate the upstream qualification gate for SprintZero projects.",
                "Use validation results to auto-fill PRD risk sections and acceptance criteria.",
                "Sell the combined flow as evidence-backed product development.",
            ],
            "Validated idea to PRD conversion rate",
        ),
    ]

    threats = [
        _swot_item(
            f"{first.name} depends on merchant belief that agent-driven purchasing is near-term; education friction can slow adoption.",
            first.challenges or first.context,
            [
                "Avoid selling a generic trust badge before agent checkout traffic exists.",
                "Anchor pilots to merchants already experimenting with agent commerce.",
                "Use FOMO messaging only after a visible agent-buyer demo works end to end.",
            ],
            "Merchant pilot activation after demo",
        ),
        _swot_item(
            f"{third.name} faces substitutes that already hold attention, especially Eventbrite, Facebook groups, Instagram, and local magazines.",
            third.competitors or third.context,
            [
                "Compete on specificity and freshness, not on being a bigger calendar.",
                "Narrow the first persona to users who need hyper-specific local culture discovery.",
                "Show source provenance so the product feels more reliable than social feeds.",
            ],
            "Repeat weekly discovery sessions",
        ),
        _swot_item(
            f"{fifth.name} can become expensive research theater if insights are not tied to buyer decisions.",
            fifth.challenges or fifth.context,
            [
                "Require every generated insight to name the decision it supports.",
                "Rank outputs by actionability, novelty, and source confidence.",
                "Delay broad crawling until one research buyer segment repeatedly pays.",
            ],
            "Paid decisions influenced by generated insights",
        ),
    ]

    return {
        "type": "quadrant",
        "title": "SWOT Strategy Canvas",
        "subtitle": f"Project-specific strategic audit for: {topic}",
        "analysis_brief": [
            f"Detected {len(projects)} project concept{'s' if len(projects) != 1 else ''}: {names}.",
            "The canvas separates near-term demo wedges from adoption, data, compute, and market-timing risks.",
            "Click any insight to open a focused workspace with suggested evidence, actions, and metrics. Export a PDF after your notes are complete.",
        ],
        "sections": [
            {"id": "strengths", "label": "Strengths", "prompt": "Internal advantages to preserve or amplify.", "items": strengths},
            {"id": "weaknesses", "label": "Weaknesses", "prompt": "Internal limitations that could slow execution.", "items": weaknesses},
            {"id": "opportunities", "label": "Opportunities", "prompt": "External openings worth exploiting.", "items": opportunities},
            {"id": "threats", "label": "Threats", "prompt": "External forces that could reduce odds of success.", "items": threats},
        ],
    }


def generate_swot(goal: str) -> dict[str, Any]:
    brief = extract_domain_brief(goal)
    topic = brief.subject
    if _is_relationship_goal(goal):
        return _relationship_swot(goal, _topic(goal))
    projects = _extract_projects(goal)
    if projects:
        return _project_specific_swot(projects, _topic(goal))

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


def _triangle_rice_rows() -> list[dict[str, Any]]:
    return [
        _rice_row(
            "Daily multi-source event ingestion agent",
            900,
            5,
            76,
            5,
            "This is the core supply engine. The idea only becomes useful if it can pull from Instagram, venue pages, Eventbrite, local publications, and manual submissions with predictable cadence.",
            [
                "Ingest events daily from 20 RTP venues, 10 Instagram accounts, Eventbrite, and 3 indie calendars.",
                "Store source URL, scrape timestamp, venue, date, genre, price, and confidence for every event.",
                "Alert a curator when a source changes format or an event cannot be parsed.",
            ],
            [
                "Reach assumes the first 100 culture-seeking users need a feed that is meaningfully fuller than Facebook groups.",
                "Impact is high because without supply, every downstream discovery feature is empty.",
                "Confidence is moderate because scraping Instagram and dead venue sites is brittle.",
            ],
        ),
        _rice_row(
            "Event deduplication, normalization, and freshness scoring",
            840,
            5,
            72,
            4,
            "The app's promise is not just more events, it is cleaner and more trustworthy local culture data. Deduplication and freshness make the experience defensible.",
            [
                "Merge duplicate event mentions across venue pages, social posts, and ticketing platforms.",
                "Display freshness badges based on source recency, venue confirmation, and duplicate agreement.",
                "Flag stale or conflicting listings for curator review before users see them.",
            ],
            [
                "Reach tracks all users because every search/feed depends on clean inventory.",
                "Impact is high because trust is the differentiator versus cluttered local groups.",
                "Effort is lower than full scraping because rules and human QA can cover early cases.",
            ],
        ),
        _rice_row(
            "Hyperlocal discovery feed with mood, genre, neighborhood, and date filters",
            760,
            4,
            78,
            3,
            "This is the user-facing wedge: people should find a highly specific night out faster than they can by searching Instagram, Facebook, and dead calendars.",
            [
                "Let users filter by mood, genre, neighborhood, date, price, indoor/outdoor, and last-minute availability.",
                "Generate weekly culture cards such as 'low-key jazz tonight' or 'open mic under $10'.",
                "Remember saved preferences and surface similar events without asking users to build a profile.",
            ],
            [
                "Reach is strong for first users because this is the visible product experience.",
                "Impact is high but depends on supply quality.",
                "Effort is contained if filters map to normalized event fields from the ingestion layer.",
            ],
        ),
        _rice_row(
            "Artist and venue opportunity portal",
            520,
            4,
            68,
            4,
            "The dual-sided portal can create supply by helping artists find open mics, booking leads, and venues that need acts. It is valuable, but liquidity risk is higher than consumer discovery.",
            [
                "Show artists open mics, submission forms, booking contacts, venue fit, and deadline reminders.",
                "Let venues submit open slots and mark recurring events as verified.",
                "Create a lead board for artists with source provenance and outreach status.",
            ],
            [
                "Reach starts smaller because artists and venues are a narrower segment than event seekers.",
                "Impact is high because supply-side participation can improve inventory quality.",
                "Confidence is lower because two-sided behavior takes more trust and onboarding.",
            ],
        ),
        _rice_row(
            "Cold-start seeding console and curator QA workflow",
            360,
            5,
            82,
            3,
            "The cold start problem is explicitly called out. A human-assisted seeding console makes the first month useful before agents are fully reliable.",
            [
                "Give curators a queue for unverified events, duplicate candidates, broken sources, and venue updates.",
                "Auto-generate missing event summaries from source snippets, then require one-click approval.",
                "Track coverage by neighborhood and genre so the first city does not feel sparse.",
            ],
            [
                "Reach is narrower because only operators use it, but it affects everyone indirectly.",
                "Impact is high because first-user usefulness depends on populated local inventory.",
                "Confidence is high because manual QA can work immediately for one region.",
            ],
        ),
        _rice_row(
            "Venue sponsorship and ticketing monetization hooks",
            430,
            3,
            62,
            3,
            "Revenue is plausible locally, but monetization should not outrank trust and supply in the first 30 days.",
            [
                "Add sponsored venue cards only after organic ranking and freshness are credible.",
                "Track ticket clicks and sponsor interest without letting paid placement pollute relevance.",
                "Create a weekly venue performance report for sponsorship conversations.",
            ],
            [
                "Reach is moderate because venue buyers are fewer than users.",
                "Impact is meaningful for monetization but premature if inventory quality is weak.",
                "Confidence is lower until venues see real local demand.",
            ],
        ),
    ]


def _feature_rows_from_projects(projects: list[ParsedProject]) -> list[dict[str, Any]]:
    text = " ".join(project.context for project in projects).lower()
    if "triangle" in text or any("triangle" in project.name.lower() for project in projects):
        return _triangle_rice_rows()

    rows: list[dict[str, Any]] = []
    for project in projects[:5]:
        lower = project.context.lower()
        if any(term in lower for term in ["trust", "badge", "agent", "procure", "protocol"]):
            rows.append(
                _rice_row(
                    f"{project.name}: machine-readable trust badge pilot",
                    620,
                    4,
                    70,
                    4,
                    "Trust infrastructure needs a concrete merchant pilot before the badge has meaning.",
                    [
                        "Create a verifiable merchant profile with audit status, refund policy, inventory reliability, and agent-readable metadata.",
                        "Demo one agent purchase flow that checks the badge before procurement.",
                        "Publish a merchant-facing proof page that explains why agent buyers should trust the store.",
                    ],
                    [
                        "Reach assumes early merchants experimenting with agent commerce.",
                        "Impact is high if agent checkout trust becomes a standard buying signal.",
                        "Confidence depends on AP2/UCP adoption and merchant education.",
                    ],
                )
            )
        elif any(term in lower for term in ["requirements", "jira", "marketplace", "vibecoding", "prd"]):
            rows.append(
                _rice_row(
                    f"{project.name}: AI requirements workshop",
                    700,
                    5,
                    74,
                    4,
                    "The narrowest valuable wedge is consensus automation before marketplace liquidity and package management.",
                    [
                        "Run an AI stakeholder interview and generate a PRD, acceptance criteria, risk register, and implementation handoff.",
                        "Add a review loop where stakeholders approve or challenge requirements before build matching.",
                        "Defer marketplace automation until PRD quality is demonstrably strong.",
                    ],
                    [
                        "Reach covers founders and product teams starting AI-native builds.",
                        "Impact is high because consensus is the bottleneck even when coding is fast.",
                        "Effort is moderate if the prototype avoids full marketplace mechanics.",
                    ],
                )
            )
        elif any(term in lower for term in ["validation", "landing", "ad", "metrics"]):
            rows.append(
                _rice_row(
                    f"{project.name}: validation experiment generator",
                    640,
                    5,
                    78,
                    3,
                    "A fast evidence report can prove demand before implementation spend.",
                    [
                        "Generate a micro-landing page, audience hypothesis, ad copy, survey prompts, and validation scorecard.",
                        "Summarize waitlist quality, click intent, user objections, and next build recommendation.",
                        "Offer founders a decision-grade PDF even if the idea fails validation.",
                    ],
                    [
                        "Reach fits founders evaluating multiple ideas.",
                        "Impact is high because it can prevent wasteful builds.",
                        "Confidence is strong because manual/ad-assisted validation can work without full automation.",
                    ],
                )
            )
        elif any(term in lower for term in ["database", "pubmed", "patent", "research", "insight"]):
            rows.append(
                _rice_row(
                    f"{project.name}: cross-corpus insight brief",
                    460,
                    4,
                    66,
                    5,
                    "The value is novel synthesis, but cost must be controlled by narrowing the corpus and buyer decision.",
                    [
                        "Connect two high-value public datasets and generate ranked interdisciplinary insight cards.",
                        "Require every insight to state the decision, source confidence, novelty, and next research path.",
                        "Cache repeated intersections before expanding to large-scale data mining.",
                    ],
                    [
                        "Reach starts narrower with researchers or technical founders.",
                        "Impact can be high if insights trigger valuable decisions.",
                        "Effort is high because retrieval, synthesis, and provenance are complex.",
                    ],
                )
            )
    return rows


def generate_rice(goal: str) -> dict[str, Any]:
    brief = extract_domain_brief(goal)
    topic = brief.subject
    projects = _extract_projects(goal)
    rows = _feature_rows_from_projects(projects) if projects else []

    if not rows:
        text = goal.lower()
        if "triangle" in text and ("event" in text or "gig" in text):
            rows = _triangle_rice_rows()

    if not rows:
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


def _hockey_stick_principles() -> list[TrizPrinciple]:
    return [
        TrizPrinciple(
            1,
            "Segmentation",
            "Separate the hockey stick into shaft, blade, hosel/heel, grip, and kick-zone modules so weight can be removed only where stiffness and impact loads allow it.",
            "A lighter stick is not one uniform material problem. The shaft needs low swing weight and torsional stiffness, while the blade needs impact toughness, puck feel, and edge durability.",
            [
                _panel(
                    "Contradiction rewrite",
                    "Frame the hockey-stick tradeoff in concrete engineering terms.",
                    [
                        "Reduce total mass and swing weight while preserving shot energy transfer, blade durability, torsional stiffness, and puck feel.",
                        "Remove material from low-load shaft zones without weakening the heel, blade edge, or lower-shaft slash-impact region.",
                        "Lower blade mass for faster handling while keeping enough damping and stiffness for passing accuracy.",
                    ],
                    value="Reduce total mass and swing weight while preserving shot energy transfer, blade durability, torsional stiffness, and puck feel.",
                    option_sets=[
                        [
                            "Reduce shaft mass while maintaining flex profile, torsional rigidity, and resistance to slash impacts.",
                            "Lower blade inertia while preserving puck feel, face stability, and edge chip resistance.",
                            "Move reinforcement out of low-stress zones and into heel, lower shaft, and blade perimeter load paths.",
                        ]
                    ],
                ),
                _panel(
                    "Material architecture",
                    "Choose material moves that fit modern composite stick construction.",
                    [
                        "Use a high-modulus unidirectional carbon fiber shaft with localized aramid or S-glass toughening in slash-prone lower-shaft zones.",
                        "Try spread-tow carbon plies to reduce resin-rich gaps and keep stiffness with less laminate mass.",
                        "Use a lightweight foam blade core with carbon skins, then reinforce the perimeter and heel with tougher fiber patches.",
                    ],
                    option_sets=[
                        [
                            "Compare standard-modulus carbon, high-modulus carbon, and hybrid carbon/aramid layups for stiffness-to-weight and impact tolerance.",
                            "Prototype a variable wall-thickness shaft: thinner upper shaft, reinforced lower shaft, and added hoop plies near the hosel.",
                            "Evaluate toughened epoxy resin systems before exotic fibers, because resin toughness often controls impact damage growth.",
                        ],
                        [
                            "Reserve boron or graphene-enhanced materials for small reinforcement zones where cost and brittleness are acceptable.",
                            "Add basalt or aramid veil layers only where blade chipping and slash impact are the dominant failure modes.",
                            "Use finite-element load maps to remove laminate from neutral/low-stress regions instead of making the whole stick thinner.",
                        ],
                    ],
                ),
                _panel(
                    "Prototype test",
                    "Pick the smallest physical test that proves the lighter design is not fragile.",
                    [
                        "Build three coupon sets: current layup, high-modulus carbon layup, and carbon/aramid hybrid; test bending stiffness, torsion, and impact damage.",
                        "Make a segmented blade/shaft prototype and compare swing weight, slap-shot deflection, wrist-shot release, and puck-feel ratings.",
                        "Run a slash-impact fixture on the lower shaft before any on-ice user testing.",
                    ],
                    option_sets=[
                        [
                            "Measure center of mass and moment of inertia, not just grams, because a lighter blade can feel faster than the same mass removed near the handle.",
                            "Use strain gauges or painted witness marks at the heel, lower shaft, and blade toe to find where mass cannot be removed.",
                            "Run cold-temperature impact tests because hockey sticks fail differently at rink temperatures than at room temperature.",
                        ]
                    ],
                ),
                _panel(
                    "Failure mode",
                    "Identify what could get worse when the stick gets lighter.",
                    [
                        "High-modulus carbon can be stiff and light but may reduce impact tolerance if not toughened with resin or hybrid fibers.",
                        "A lighter blade can reduce puck feel if the foam core and damping layers are over-thinned.",
                        "Removing wall thickness in the lower shaft can create slash-impact cracks even if lab bending stiffness looks acceptable.",
                    ],
                    option_sets=[
                        [
                            "Watch for brittle heel failures, blade-face delamination, toe chipping, and torsional flutter during hard passes.",
                            "Do not treat advertised low weight as success unless durability, flex repeatability, and player feel survive testing.",
                            "Cost and repairability may worsen if exotic reinforcement is applied across the whole stick instead of high-load zones.",
                        ]
                    ],
                ),
            ],
        ),
        TrizPrinciple(
            31,
            "Porous materials",
            "Use lightweight internal cores and controlled hollow spaces so the stick keeps outer shell stiffness without carrying unnecessary solid material.",
            "Modern sticks already exploit hollow composite shafts and foam blade cores; the inventive move is making internal structure more deliberate.",
            [
                _panel(
                    "Core strategy",
                    "Select where hollow, foam, or lattice structure can reduce mass.",
                    [
                        "Keep the shaft as a hollow composite tube but vary wall thickness by load zone.",
                        "Use blade foam density gradients: denser near heel and perimeter, lighter in lower-stress central zones.",
                        "Test ribbed or lattice blade cores only if they improve puck feel and resist water ingress.",
                    ],
                ),
                _panel(
                    "Prototype test",
                    "Prove the lighter core survives the use case.",
                    [
                        "Compare blade torsional stiffness, rebound consistency, and moisture ingress after impact.",
                        "Run repeated slap-shot and board-impact cycles on baseline and lightweight core prototypes.",
                        "Measure acoustic/vibration feedback because player feel can degrade before structural failure.",
                    ],
                ),
                _panel(
                    "Failure mode",
                    "Watch for hidden core-driven failures.",
                    [
                        "A too-light blade core can create dead spots, delamination, or edge collapse.",
                        "Internal voids can concentrate stress if the laminate is not supported during impact.",
                        "Foam density changes can shift balance and alter release feel even when total weight improves.",
                    ],
                ),
            ],
        ),
        TrizPrinciple(
            35,
            "Parameter change",
            "Change fiber orientation, modulus, resin toughness, wall thickness, balance point, and kick-zone geometry instead of only chasing lower total weight.",
            "The user asked for lighter, but performance is governed by stiffness-to-weight, impact energy absorption, and moment of inertia.",
            [
                _panel(
                    "Parameter map",
                    "Pick the parameters to vary in the experiment.",
                    [
                        "Vary fiber orientation: 0-degree plies for bending stiffness, +/-45-degree plies for torsion, 90-degree hoop plies for crush resistance.",
                        "Move mass reduction toward the blade and lower shaft first because it changes swing weight more than handle trimming.",
                        "Use a tougher resin or local aramid patches where impact failure dominates instead of globally adding carbon.",
                    ],
                ),
                _panel(
                    "Prototype test",
                    "Run a design-of-experiments instead of one-off samples.",
                    [
                        "Build a 2x2 test: standard vs high-modulus carbon and normal vs toughened resin.",
                        "Measure mass, balance point, flex profile, torsional stiffness, impact survival, and player-rated puck feel.",
                        "Use the best coupon result to decide the first full-stick layup.",
                    ],
                ),
                _panel(
                    "Failure mode",
                    "Name what a parameter change might break.",
                    [
                        "Changing kick-zone geometry can alter release timing even if weight improves.",
                        "Higher stiffness can make the stick feel harsher and reduce puck handling confidence.",
                        "Moving the balance point can feel worse even if scale weight is lower.",
                    ],
                ),
            ],
        ),
        TrizPrinciple(
            40,
            "Composite materials",
            "Use a hybrid composite instead of a single material: carbon for stiffness-to-weight, aramid/S-glass for toughness, toughened epoxy for damage resistance, and foam/core structures for blade mass control.",
            "The hockey-stick problem is naturally composite: no single material optimizes lightness, shot power, slash resistance, blade feel, and cost.",
            [
                _panel(
                    "Material shortlist",
                    "Create a grounded shortlist before exotic materials distract the build.",
                    [
                        "Baseline: unidirectional carbon fiber/epoxy shaft with foam-core carbon blade.",
                        "Durability hybrid: carbon primary plies plus aramid or S-glass in lower shaft, heel, and blade perimeter.",
                        "Advanced test: high-modulus or spread-tow carbon with toughened epoxy; reserve boron or graphene-enhanced resin for small reinforcement trials.",
                    ],
                    option_sets=[
                        [
                            "Avoid aluminum or titanium as primary stick materials for the V1 unless the goal is a specialty training stick; composites dominate because stiffness-to-weight is better.",
                            "Use wood only as a control sample for puck feel and damping, not as the path to minimum mass.",
                            "Consider recycled carbon only if sustainability is a requirement, because fiber consistency and certification can complicate performance claims.",
                        ]
                    ],
                ),
                _panel(
                    "Supplier question",
                    "Ask the question a materials engineer or vendor must answer.",
                    [
                        "What is the specific modulus, tensile strength, impact toughness, and resin system for the proposed carbon prepreg?",
                        "How does the layup perform after cold-temperature impact and cyclic slap-shot loading?",
                        "What mass reduction comes from fiber choice versus layup optimization versus blade core redesign?",
                    ],
                ),
                _panel(
                    "Failure mode",
                    "Keep the advanced material honest.",
                    [
                        "Exotic fibers can increase cost and brittleness while producing only small weight savings.",
                        "Marketing materials may cite carbon grade without revealing layup, resin, void content, or durability.",
                        "A material that wins coupon stiffness can still lose full-stick feel.",
                    ],
                ),
            ],
        ),
        TrizPrinciple(
            3,
            "Local quality",
            "Make high-load regions strong and low-load regions light instead of applying the same laminate everywhere.",
            "The stick has very different local jobs: the handle transmits grip, the shaft stores/release energy, the heel takes stress, and the blade controls feel.",
            [
                _panel(
                    "Load-zone design",
                    "Choose where the stick deserves different construction.",
                    [
                        "Reinforce the heel and lower shaft with tougher hybrid plies while thinning the upper shaft wall.",
                        "Use blade-edge reinforcement for chipping without adding mass to the entire face.",
                        "Tune the kick zone locally so weight reduction does not break shot timing.",
                    ],
                ),
                _panel(
                    "Prototype test",
                    "Validate local reinforcement with targeted loads.",
                    [
                        "Test heel bending, lower-shaft slash impact, blade toe impact, and full-stick flex separately.",
                        "Measure whether local reinforcement changes balance point or release feel.",
                        "Run player blind tests on baseline and load-zone prototypes.",
                    ],
                ),
                _panel(
                    "Failure mode",
                    "Watch for stress transfer created by local reinforcement.",
                    [
                        "A reinforced region can move failure to the neighboring thin region.",
                        "Local stiffness jumps can create harsh feel or unpredictable flex.",
                        "Manufacturing complexity can erase the weight and cost advantage.",
                    ],
                ),
            ],
        ),
    ]


def _cnc_triz_principles() -> list[TrizPrinciple]:
    return [
        TrizPrinciple(
            10,
            "Preliminary action",
            "Move expensive validation before live machining: simulate, backplot, dry-run, and risk-score optimized CNC/G-code before a spindle ever cuts material.",
            "The contradiction is speed versus safety. A CNC optimization algorithm must reduce cycle time without causing crashes, scrap, tool wear, or tolerance failures.",
            [
                _panel(
                    "Contradiction rewrite",
                    "Frame the CNC commercialization contradiction in production terms.",
                    [
                        "Improve CNC cycle time and programming efficiency without increasing crash risk, scrap, tool wear, or machinist mistrust.",
                        "Let the algorithm suggest feed/speed, toolpath order, and air-cut reductions while preserving controller/post-processor safety.",
                        "Increase automation without removing human review from high-risk machining decisions.",
                    ],
                    value="Improve CNC cycle time and programming efficiency without increasing crash risk, scrap, tool wear, or machinist mistrust.",
                ),
                _panel(
                    "Inventive move",
                    "Move proof and safety checks before production use.",
                    [
                        "Generate an optimization report first, then require simulation and CAM programmer approval before rewriting production files.",
                        "Run every optimized file through a controller-aware backplot/simulation gate.",
                        "Score changes by risk: low-risk air-cut and tool-order improvements can be automated before feed/speed changes.",
                    ],
                ),
                _panel(
                    "Prototype",
                    "Build the smallest safe test.",
                    [
                        "Use 10 anonymized CNC files and compare baseline cycle time, optimized estimate, simulation pass, and machinist acceptance.",
                        "Pilot on one machine/controller family before claiming general CNC compatibility.",
                        "Offer an ROI report instead of a production-ready rewritten file in the first customer test.",
                    ],
                ),
                _panel(
                    "Failure mode",
                    "Name what can break trust.",
                    [
                        "An optimization that passes math but fails controller-specific behavior can scrap a part or damage a tool.",
                        "Customers may reject cloud upload if part files are proprietary or defense/aerospace sensitive.",
                        "A cycle-time win can be meaningless if it worsens surface finish, tolerance, or tool life.",
                    ],
                ),
            ],
        ),
        TrizPrinciple(
            24,
            "Intermediary",
            "Introduce a machinist/CAM programmer review layer between the algorithm and production CNC files.",
            "The product can commercialize faster if it begins as trusted decision support rather than full autonomous file rewriting.",
            [
                _panel(
                    "Intermediary design",
                    "Choose the trust layer.",
                    [
                        "Use a review queue showing original G-code/CAM intent, proposed change, expected savings, and risk reason.",
                        "Add explainability: why the toolpath order, feed, speed, or retract move changed.",
                        "Let users approve categories of low-risk changes while locking high-risk changes behind review.",
                    ],
                ),
                _panel(
                    "Metric",
                    "Measure whether the intermediary is earning trust.",
                    [
                        "Percentage of recommendations accepted by CAM programmers without correction.",
                        "Number of unsafe recommendations caught before simulation or live machining.",
                        "Time from CNC file upload to approved optimization report.",
                    ],
                ),
                _panel(
                    "Failure mode",
                    "Avoid becoming a slow consulting workflow.",
                    [
                        "If every change needs deep expert review, the product may not scale beyond services.",
                        "If explanations are too technical for owners but too shallow for machinists, neither buyer trusts the product.",
                        "If approval UX is painful, users may return to existing CAM workflows.",
                    ],
                ),
            ],
        ),
        TrizPrinciple(
            3,
            "Local quality",
            "Optimize different CNC file regions differently: air cuts, roughing, finishing, tool changes, retracts, and tolerance-critical moves should not share one risk rule.",
            "A global optimization may be unsafe. CNC value comes from local improvements that respect machining context.",
            [
                _panel(
                    "Segmentation map",
                    "Split the CNC file into risk zones.",
                    [
                        "Separate air-cut removal, rapid moves, tool change order, roughing feeds, finishing feeds, and tolerance-critical surfaces.",
                        "Automate low-risk cycle-time wins first; only recommend high-risk geometry/feed changes.",
                        "Expose which zones were untouched because risk or missing metadata was too high.",
                    ],
                ),
                _panel(
                    "Prototype",
                    "Test one local optimization class first.",
                    [
                        "Start with air-cut and retract-path reduction because it can reduce time without changing cutting conditions.",
                        "Benchmark roughing-only optimization separately from finishing passes.",
                        "Report savings by zone so buyers understand where ROI comes from.",
                    ],
                ),
                _panel(
                    "Failure mode",
                    "Watch local optimization side effects.",
                    [
                        "Changing tool order can affect setup assumptions or fixture access.",
                        "Reducing retracts can introduce collision risk if fixtures are not modeled.",
                        "Optimizing roughing may shift heat, chip evacuation, or tool load in ways the file alone does not reveal.",
                    ],
                ),
            ],
        ),
        TrizPrinciple(
            25,
            "Self-service",
            "Let the CNC file, machine profile, material, tool library, and simulation result drive the recommendation rather than forcing the user to describe everything manually.",
            "Commercialization improves when the product can infer enough context to be useful while clearly asking for missing data.",
            [
                _panel(
                    "Required context",
                    "Define what the algorithm must know.",
                    [
                        "Require machine/controller, material, tool library, tolerance criticality, fixture assumptions, and post-processor where possible.",
                        "Ask for missing fields only when they change safety or ROI.",
                        "Show confidence by recommendation, not just one global score.",
                    ],
                ),
                _panel(
                    "Metric",
                    "Measure self-service usefulness.",
                    [
                        "Percentage of uploaded files that reach a recommendation without support.",
                        "Number of missing-context prompts per file.",
                        "Pilot user confidence after reviewing the output.",
                    ],
                ),
                _panel(
                    "Failure mode",
                    "Avoid false confidence.",
                    [
                        "Inferring missing machine context can create unsafe recommendations.",
                        "Too many required fields can kill adoption before users see value.",
                        "A black-box confidence score will not satisfy expert CAM programmers.",
                    ],
                ),
            ],
        ),
    ]


def _relationship_triz_principles(goal: str) -> list[TrizPrinciple]:
    person = _relationship_name(goal)
    return [
        TrizPrinciple(
            1,
            "Segmentation",
            f"Separate the breakup decision about {person} into values, daily connection, family expectations, travel/lifestyle, household boundaries, communication safety, and repair willingness.",
            "A relationship decision becomes vague and overwhelming when every hurt is treated as one giant verdict.",
            [
                _panel(
                    "Contradiction rewrite",
                    "Turn the emotional conflict into a clear relationship contradiction.",
                    [
                        f"I want freedom to learn, create, travel, and dream while also wanting a partner relationship with {person} that includes daily connection, respect, and shared future direction.",
                        f"I want to stop feeling empty and exhausted, but I do not want to make a breakup decision from contempt, sarcasm, or one flooded conversation.",
                        f"I want clarity about family, travel, home life, and emotional availability without forcing {person} to become someone she is not.",
                    ],
                    value=f"I want freedom to learn, create, travel, and dream while also wanting a partner relationship with {person} that includes daily connection, respect, and shared future direction.",
                    option_sets=[
                        [
                            f"I need to know whether {person} and I can repair connection patterns before deciding whether breakup is the best choice.",
                            "I need to distinguish incompatibility from solvable habits, stress reactions, and poor conflict process.",
                            "I need a decision process that protects dignity for both people even if the outcome is separation.",
                        ]
                    ],
                ),
                _panel(
                    "Inventive move",
                    "Break the decision into smaller tests instead of treating breakup as the only next move.",
                    [
                        "Create four columns: core values, negotiable preferences, repairable habits, and immediate boundaries.",
                        f"Ask {person} for one structured conversation about expectations: salary, family, travel, time with Antuan, TV/reading differences, and home/pet boundaries.",
                        "Run a 30-day repair sprint only if both people agree to observable behaviors, not vague promises.",
                    ],
                    option_sets=[
                        [
                            "Separate the pet-shop/home conflict from deeper issues of being heard, respected, and allowed to have adult boundaries.",
                            "Separate travel preferences from the deeper question: do both people want shared wonder, learning, and family time?",
                            "Separate emotional exhaustion from the decision itself: first calm the process, then judge compatibility.",
                        ],
                        [
                            "Define two stay conditions: mutual repair effort and respectful conflict. Define two leave conditions: contempt continues or core life goals are incompatible.",
                            "Use a therapist/mediator if the two of you cannot discuss family, money, travel, and connection without shutdown.",
                            "Prepare a respectful separation plan in parallel so staying is a choice, not inertia.",
                        ],
                    ],
                ),
                _panel(
                    "Prototype",
                    "Choose a humane experiment before an irreversible decision.",
                    [
                        "Schedule a 60-minute calm talk with an agenda: needs, expectations, repair willingness, and what each person will actually change for 30 days.",
                        "Plan one low-pressure shared activity that is not TV-only or wine-only: music history, a walk, a museum, travel dreaming, or time with Antuan.",
                        "Write a private decision memo after the talk: what changed, what did not, and whether you felt more respected or more alone.",
                    ],
                    option_sets=[
                        [
                            "Use a no-sarcasm rule for the next hard conversation; restart later if either person mocks, shuts down, or escalates.",
                            "Ask each person to bring a list of expectations, including money/salary, family, travel, home priorities, and emotional connection.",
                            "End the test early if either person feels unsafe, coerced, or repeatedly demeaned.",
                        ]
                    ],
                ),
                _panel(
                    "Failure mode",
                    "Name what could go wrong with this approach.",
                    [
                        "Segmentation can become analysis paralysis if you keep sorting issues but avoid the painful decision.",
                        f"{person} may experience the framework as a trial or indictment if it is presented harshly.",
                        "A repair sprint is not useful if only one person is participating or if contempt remains in the room.",
                    ],
                    option_sets=[
                        [
                            "Do not use the canvas as a script to prosecute Hollie. Use it to prepare calmer questions and your own boundaries.",
                            "Do not let a single good date erase chronic incompatibilities if the core issues remain unchanged.",
                            "Do not let fear of grief keep you in a relationship that both people know is no longer mutual.",
                        ]
                    ],
                ),
            ],
        ),
        TrizPrinciple(
            10,
            "Preliminary action",
            "Do emotional and logistical preparation before a breakup-or-stay conversation so the moment is less reactive.",
            "The expensive part is not only the decision; it is the damage caused by making it while flooded.",
            [
                _panel(
                    "Preparation",
                    "Prepare before the decisive talk.",
                    [
                        "Write what you want, what you expect, what you can offer, and what you cannot keep doing.",
                        f"Ask {person} to prepare her own list before the conversation instead of forcing answers in the moment.",
                        "Choose a calm time, no alcohol, no audience, no sarcasm, and a stop rule if either person escalates.",
                    ],
                ),
                _panel(
                    "Prototype",
                    "Run the prepared conversation.",
                    [
                        "Use one prompt: 'Do we both want to repair this, and what behavior would prove it over the next 30 days?'",
                        "Ask: 'What would make you feel loved by me, and what would make me feel loved by you?'",
                        "Ask directly whether family, travel, money, and home priorities are compatible enough to build around.",
                    ],
                ),
                _panel(
                    "Failure mode",
                    "Watch for false clarity.",
                    [
                        "Preparation can become a speech instead of a dialogue.",
                        "A beautiful conversation can still fail if no behavior changes afterward.",
                        "If either person uses threats, contempt, or coercion, preparation is not enough; get outside support.",
                    ],
                ),
            ],
        ),
        TrizPrinciple(
            15,
            "Dynamics",
            "Replace a permanent yes/no decision with a time-bound adaptive experiment when safety allows.",
            "Some uncertainty can only be resolved by observing changed behavior over time.",
            [
                _panel(
                    "Inventive move",
                    "Make the relationship test dynamic and time-boxed.",
                    [
                        "Try a 30-day repair agreement with weekly check-ins and visible behavior commitments from both people.",
                        "Try a short structured separation if both people need space to think without daily escalation.",
                        "Change the connection routine: one shared activity per week chosen alternately by each person.",
                    ],
                ),
                _panel(
                    "Metric",
                    "Measure behavior, not promises.",
                    [
                        "Track whether both people initiate connection without resentment.",
                        "Track whether hard topics can be discussed without shutdown or ridicule.",
                        "Track whether each person makes one concrete compromise that matters to the other.",
                    ],
                ),
                _panel(
                    "Failure mode",
                    "Avoid endless limbo.",
                    [
                        "A dynamic experiment needs a decision date.",
                        "If the same painful loop repeats, the experiment is evidence, not failure.",
                        "Do not use time-boxing to pressure someone into family, travel, or lifestyle goals they do not want.",
                    ],
                ),
            ],
        ),
        TrizPrinciple(
            24,
            "Intermediary",
            "Use a therapist, mediator, written agenda, or trusted neutral process between the hurt and the decision.",
            "When the couple cannot talk without shutdown, the interface between people may need redesign.",
            [
                _panel(
                    "Intermediary choice",
                    "Choose a buffer that protects both people.",
                    [
                        "Use a couples therapist if both people want repair but cannot discuss hard topics safely.",
                        "Use a written agenda if live conversation becomes chaotic.",
                        "Use separate individual counseling or a grounded friend if you need clarity before speaking.",
                    ],
                ),
                _panel(
                    "Conversation structure",
                    "Make the intermediary practical.",
                    [
                        "Each person gets uninterrupted time to state needs, fears, and desired future.",
                        "No diagnosis, insults, sarcasm, or parent-child framing.",
                        "End with specific next actions: repair sprint, planned separation, or another structured session.",
                    ],
                ),
                _panel(
                    "Failure mode",
                    "Name where mediation can fail.",
                    [
                        "An intermediary cannot create desire if one person is already done.",
                        "A written agenda can still become a weapon if it is used to win.",
                        "Therapy is not a substitute for safety planning if there is abuse or coercion.",
                    ],
                ),
            ],
        ),
        TrizPrinciple(
            35,
            "Parameter change",
            "Change frequency, format, setting, and intensity of connection attempts before concluding nothing can work.",
            "The Elvis movie example may reflect a mismatch in connection format, not just lack of love.",
            [
                _panel(
                    "Parameter map",
                    "Change one relationship parameter at a time.",
                    [
                        "Change format: from TV/movie bids to walks, music, travel planning, cooking, or short shared rituals.",
                        "Change frequency: one planned quality-time block instead of hoping connection appears.",
                        "Change intensity: discuss family, money, travel, and home boundaries in separate talks rather than all at once.",
                    ],
                ),
                _panel(
                    "Prototype",
                    "Test the parameter change.",
                    [
                        f"Ask {person}: 'What kind of shared time would actually feel good to you this week?'",
                        "Create one shared travel-dream session where wine, wonder, family time, and budget all get represented.",
                        "Create one home-boundary conversation about pets/cat structures that avoids insults and focuses on shared living standards.",
                    ],
                ),
                _panel(
                    "Failure mode",
                    "Know when parameter tuning is not enough.",
                    [
                        "If core values are incompatible, changing date format will not solve the relationship.",
                        "If one person refuses all bids for connection, the format is not the main issue.",
                        "If resentment is too high, small experiments may need to wait until the conflict process is safer.",
                    ],
                ),
            ],
        ),
    ]


def generate_triz(goal: str) -> dict[str, Any]:
    topic = _topic(goal)
    hockey = "hockey" in goal.lower() and "stick" in goal.lower()
    cnc = any(term in goal.lower() for term in ["cnc", "g-code", "gcode", "toolpath", "machining"])
    relationship = _is_relationship_goal(goal)
    principles = _hockey_stick_principles() if hockey else (_cnc_triz_principles() if cnc else (_relationship_triz_principles(goal) if relationship else TRIZ_STARTERS))
    contradiction = {
        "improving": (
            "Reduce hockey-stick mass and swing weight for faster handling and release"
            if hockey
            else (
                "Reduce CNC cycle time, programming effort, and machine-hour cost with algorithmic optimization"
                if cnc
            else (
                "Make a clear stay-or-breakup decision while preserving dignity, safety, and honest understanding"
                if relationship
                else "The desired improvement the user wants to maximize"
            )
            )
        ),
        "worsening": (
            "Less material can reduce impact durability, torsional stiffness, shot energy transfer, and puck feel"
            if hockey
            else (
                "Unsafe toolpath changes can increase crash risk, scrap, tool wear, tolerance failures, or machinist mistrust"
                if cnc
            else (
                "Acting too fast can cause regret or harm; delaying too long can deepen resentment and loneliness"
                if relationship
                else "The system property that appears to get worse when improving it"
            )
            )
        ),
        "prompt": (
            "Rewrite these two fields into a crisp material/design contradiction before selecting a principle."
            if hockey
            else (
                "Rewrite these two fields into a crisp CNC production contradiction before selecting a principle."
                if cnc
            else (
                "Rewrite these two fields into a humane relationship contradiction before selecting a principle."
                if relationship
                else "Rewrite these two fields into a crisp contradiction before selecting a principle."
            )
            )
        ),
    }
    analysis_brief = (
        [
            "Research brief: modern performance hockey sticks are typically composite systems, not simple metal or wood parts: carbon fiber/epoxy shafts, foam-core composite blades, and localized reinforcement drive the design space.",
            "Material shortlist: high-modulus or spread-tow carbon can reduce mass, aramid/Kevlar or S-glass can improve impact toughness, toughened epoxy can slow damage growth, and boron/graphene-style additives should be tested only in small high-load zones.",
            "The TRIZ contradiction is mass versus durability/feel. A good answer should change layup, load-zone reinforcement, balance point, and blade core architecture, then validate with cold impact, torsion, flex, and player-feel tests.",
        ]
        if hockey
        else [
            "Research brief: CNC/CAM optimization is valuable only when it safely improves cycle time, tool changes, air cuts, feed/speed strategy, or programming effort without breaking controller-specific assumptions.",
            "Commercialization constraint: job shops and manufacturing engineers will demand simulation, explainability, file security, controller/post-processor compatibility, and clear ROI before trusting optimized CNC output.",
            "The TRIZ contradiction is automation versus safety. The best first product may be a reviewed optimization report and simulation-ready recommendation, not fully autonomous production file rewriting.",
        ]
        if cnc
        else [
            "OmniFrame detected a relationship decision and adapted TRIZ away from engineering language into structured conflict-resolution moves.",
            "The core contradiction is clarity versus care: you want a true decision about Hollie without making it from contempt, exhaustion, or a single escalated moment.",
            "Use these principles to separate issues, prepare a calm conversation, test repair willingness, consider mediation, or plan a respectful separation.",
        ]
        if relationship
        else [
            "OmniFrame selected TRIZ because the prompt implies a constraint conflict.",
            "Choose a principle to open a focused workspace with generated moves, prototypes, and failure checks.",
        ]
    )
    return {
        "type": "contradiction",
        "title": "TRIZ Contradiction Canvas",
        "subtitle": f"Inventive problem-solving for: {topic}",
        "analysis_brief": analysis_brief,
        "contradiction": contradiction,
        "principles": [_triz_principle_dict(principle) for principle in principles],
        "solution_cards": [
            {
                "title": "Load-zone composite layup" if hockey else ("Simulation-first optimization" if cnc else "Separate in time"),
                "body": (
                    "Use high stiffness-to-weight carbon where bending loads dominate, but add toughening plies only in heel, lower-shaft, and blade-edge impact zones."
                    if hockey
                    else (
                        "Generate a reviewed optimization report and simulation-ready CNC output before any live machine run."
                        if cnc
                        else "Make the system behave one way during exploration and another way during execution."
                    )
                ),
            },
            {
                "title": "Blade core redesign" if hockey else ("Risk-zoned toolpath changes" if cnc else "Separate in structure"),
                "body": (
                    "Reduce blade inertia with a tuned foam or ribbed core while preserving perimeter stiffness, puck feel, and water/damage resistance."
                    if hockey
                    else (
                        "Automate low-risk air-cut and ordering improvements before recommending high-risk feed, speed, or geometry changes."
                        if cnc
                        else "Split the fragile or expensive part away from the part that must move quickly."
                    )
                ),
            },
            {
                "title": "Test before exotic materials" if hockey else ("Machinist review layer" if cnc else "Introduce a mediation layer"),
                "body": (
                    "Run coupon and full-stick tests for flex, torsion, cold impact, cyclic shot loading, balance point, and player feel before choosing boron, graphene, or other premium additives."
                    if hockey
                    else (
                        "Use a CAM programmer approval queue to convert a black-box algorithm into trusted decision support."
                        if cnc
                        else "Use an adapter, queue, policy engine, or human review gate to absorb the conflict."
                    )
                ),
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


def generate_lean_startup(goal: str) -> dict[str, Any]:
    brief = extract_domain_brief(goal)
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


def generate_okrs(goal: str) -> dict[str, Any]:
    brief = extract_domain_brief(goal)
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


def generate_porters_five_forces(goal: str) -> dict[str, Any]:
    brief = extract_domain_brief(goal)
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


def generate_pestle(goal: str) -> dict[str, Any]:
    brief = extract_domain_brief(goal)
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


GENERATORS = {
    "swot": generate_swot,
    "lean_startup": generate_lean_startup,
    "okrs": generate_okrs,
    "porters_five_forces": generate_porters_five_forces,
    "pestle": generate_pestle,
    "rice": generate_rice,
    "triz": generate_triz,
}


def build_canvas(framework_id: str, goal: str) -> dict[str, Any]:
    return GENERATORS[framework_id](goal)
