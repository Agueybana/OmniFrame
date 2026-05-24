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
    return cleaned[: limit - 1].rstrip(" ,.;") + "."


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


def _panel(title: str, prompt: str, options: list[str], value: str = "") -> dict[str, Any]:
    return {
        "title": title,
        "prompt": prompt,
        "options": options,
        "value": value,
    }


def _swot_item(text: str, rationale: str, options: list[str], metric: str) -> dict[str, Any]:
    return {
        "text": _compact(text, 260),
        "rationale": _compact(rationale, 320),
        "metric": _compact(metric, 180),
        "options": [_compact(option, 220) for option in options],
        "drilldown": {
            "description": "Convert this strategic observation into evidence, decisions, and execution checks.",
            "panels": [
                _panel(
                    "Evidence to verify",
                    "Pick or edit the strongest proof that should support this claim.",
                    options[:2] + [f"Interview 5 target users about: {text}"],
                    value=options[0] if options else "",
                ),
                _panel(
                    "Strategic action",
                    "Choose the move this insight should trigger next.",
                    [
                        f"Turn this into a 7-day validation sprint: {text}",
                        "Assign one owner, one decision deadline, and one measurable output.",
                        "Defer this until the highest-risk assumption has evidence.",
                    ],
                ),
                _panel(
                    "Watch metric",
                    "Select the metric that should prove this insight mattered.",
                    [
                        metric,
                        "Evidence collected per week",
                        "Decision confidence delta after validation",
                    ],
                ),
            ],
        },
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
    topic = _topic(goal)
    projects = _extract_projects(goal)
    if projects:
        return _project_specific_swot(projects, topic)

    return {
        "type": "quadrant",
        "title": "SWOT Strategy Canvas",
        "subtitle": f"Baseline audit for: {topic}",
        "analysis_brief": [
            "No full project table was detected, so OmniFrame built a strategic baseline from the goal language.",
            "Use the focused workspaces to convert each observation into evidence, actions, and metrics before exporting.",
        ],
        "sections": [
            {
                "id": "strengths",
                "label": "Strengths",
                "prompt": "Internal advantages to preserve or amplify.",
                "items": [
                    _swot_item(
                        f"Existing capability could accelerate {topic.lower()} if it is made explicit and reusable.",
                        "The goal implies there is already enough strategic intent to start mapping assets.",
                        [
                            "List the proprietary data, relationships, audience access, or execution speed already available.",
                            "Separate true advantages from ordinary table stakes.",
                            "Turn the strongest advantage into a proof point for the first demo.",
                        ],
                        "Time saved or conversion lift from the advantage",
                    ),
                    _swot_item(
                        "Differentiated expertise, relationships, or brand trust can reduce launch friction.",
                        "Early adoption often depends on credibility before the product has full maturity.",
                        [
                            "Identify who already trusts the team and why.",
                            "Convert existing trust into a pilot, testimonial, or distribution channel.",
                            "Document the promise users should believe on first contact.",
                        ],
                        "Pilot conversion from warm channels",
                    ),
                    _swot_item(
                        "An operational asset that competitors would struggle to copy can become the strategic center.",
                        "The most useful SWOT strength is one that changes what the team should build first.",
                        [
                            "Name the asset a competitor cannot easily buy, scrape, or hire.",
                            "Tie that asset to one workflow the prototype should make visible.",
                            "Protect the asset by turning it into data, process, or user habit.",
                        ],
                        "Defensible workflow usage",
                    ),
                ],
            },
            {
                "id": "weaknesses",
                "label": "Weaknesses",
                "prompt": "Internal limitations that could slow execution.",
                "items": [
                    _swot_item(
                        "Skill, budget, data, or process gaps can make the first version feel less credible than the idea.",
                        "The first release has to prove the core job, not the whole vision.",
                        [
                            "Cut the first demo to one promise that can be verified in a week.",
                            "List missing data and assign a temporary manual workaround.",
                            "Treat unclear ownership as a launch blocker.",
                        ],
                        "Blocked assumptions resolved per week",
                    ),
                    _swot_item(
                        "A hidden assumption may need validation before scaling.",
                        "Strategic risk is highest when the team treats an unproven belief as settled.",
                        [
                            "Write the assumption that would kill the project if false.",
                            "Choose one cheap test that can disprove it quickly.",
                            "Document what result would change the roadmap.",
                        ],
                        "Assumption kill/pass decision rate",
                    ),
                    _swot_item(
                        "A dependency could become the bottleneck once users arrive.",
                        "Bottlenecks often appear in data freshness, review quality, integrations, or support.",
                        [
                            "Name the dependency that cannot be allowed to fail silently.",
                            "Add a fallback path before launch.",
                            "Instrument dependency health in the first build.",
                        ],
                        "Dependency failure recovery time",
                    ),
                ],
            },
            {
                "id": "opportunities",
                "label": "Opportunities",
                "prompt": "External openings worth exploiting.",
                "items": [
                    _swot_item(
                        "A market shift, customer pain, or regulatory change may create urgency.",
                        "External urgency changes how aggressively the prototype should be positioned.",
                        [
                            "Identify the customer pain that is getting worse right now.",
                            "Convert that pain into a headline promise and one measurable outcome.",
                            "Find the niche where urgency is strongest and alternatives are weakest.",
                        ],
                        "Urgent problem interviews completed",
                    ),
                    _swot_item(
                        "A partnership or distribution channel could compound reach faster than paid acquisition.",
                        "Strategy improves when distribution is designed with the product, not added after.",
                        [
                            "List channels with existing trust in the target user group.",
                            "Offer a partner-visible artifact they can share.",
                            "Measure referred usage quality instead of raw clicks.",
                        ],
                        "Qualified referred activation",
                    ),
                    _swot_item(
                        "An underserved segment may reward speed and relevance over completeness.",
                        "The first wedge should be narrow enough that specificity beats incumbents.",
                        [
                            "Choose one underserved segment and remove everything not needed for them.",
                            "Use direct user language in the first canvas/report.",
                            "Make one workflow feel finished even if the platform is early.",
                        ],
                        "Segment-specific task success",
                    ),
                ],
            },
            {
                "id": "threats",
                "label": "Threats",
                "prompt": "External forces that could reduce odds of success.",
                "items": [
                    _swot_item(
                        "A competitive response, substitute, or switching-cost issue could lower adoption.",
                        "Threats matter when they change the wedge, pricing, or proof required.",
                        [
                            "Name the substitute users already tolerate.",
                            "Explain why the new workflow is 10x clearer, fresher, faster, or safer.",
                            "Test whether users switch behavior, not just whether they like the concept.",
                        ],
                        "Substitute-to-product switch rate",
                    ),
                    _swot_item(
                        "Technical, legal, or adoption risk outside direct control could slow the project.",
                        "External dependencies should have fallback paths in the prototype plan.",
                        [
                            "Identify the risk the team cannot directly control.",
                            "Create a fallback that still proves the product promise.",
                            "Add a visible confidence score where uncertainty remains.",
                        ],
                        "Fallback path readiness",
                    ),
                    _swot_item(
                        "Timing risk can close the market window before launch.",
                        "The first version should prove momentum before the opportunity cools.",
                        [
                            "Define what must be learned in 30 days.",
                            "Cut any feature that does not create evidence.",
                            "Use the report export as a decision artifact for stakeholders.",
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
        "options": [_compact(option, 220) for option in options],
        "evidence": [_compact(item, 220) for item in evidence],
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
            ),
            _panel(
                "Reach evidence",
                "Choose what should justify the reach estimate.",
                evidence,
                value=evidence[0] if evidence else "",
            ),
            _panel(
                "Risk reducer",
                "Pick a way to increase confidence or reduce effort.",
                [
                    "Ship a concierge/manual version before automating the full workflow.",
                    "Instrument the first user action that proves demand.",
                    "Cut nonessential UI until the scoring assumption is validated.",
                ],
            ),
            _panel(
                "Acceptance signal",
                "Define what makes this initiative complete enough for the next planning pass.",
                [
                    f"Score improves because confidence rises above {min(confidence + 10, 95)}% without increasing effort.",
                    "Users complete the core task without a support prompt.",
                    "The exported report explains the decision well enough for stakeholders.",
                ],
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
    topic = _topic(goal)
    projects = _extract_projects(goal)
    rows = _feature_rows_from_projects(projects) if projects else []

    if not rows:
        text = goal.lower()
        if "triangle" in text and ("event" in text or "gig" in text):
            rows = _triangle_rice_rows()

    if not rows:
        rows = [
            _rice_row(
                "Validate highest-risk assumption",
                800,
                3,
                80,
                2,
                "The fastest path is to identify the belief most likely to invalidate the roadmap.",
                [
                    "Write one falsifiable assumption and run a 5-user evidence sprint.",
                    "Create a landing-page or concierge workflow before building the full product.",
                    "Define the result that would stop, pivot, or accelerate the project.",
                ],
                [
                    "Reach is broad because every roadmap option depends on assumption clarity.",
                    "Impact is moderate to high because invalid assumptions waste engineering time.",
                    "Effort is low if the test is scoped to one week.",
                ],
            ),
            _rice_row(
                "Ship narrow prototype for the strongest user segment",
                500,
                4,
                70,
                4,
                "A focused prototype creates better evidence than a broad feature set.",
                [
                    "Choose one user segment, one urgent job, and one workflow that feels complete.",
                    "Use generated copy and sample data to make the demo decision-grade.",
                    "Instrument completion, confusion, and willingness-to-pay signals.",
                ],
                [
                    "Reach is narrower because the first segment is intentionally focused.",
                    "Impact is high because it creates tangible adoption evidence.",
                    "Confidence is moderate until user testing starts.",
                ],
            ),
            _rice_row(
                "Instrument decision and adoption metrics",
                1000,
                2,
                90,
                2,
                "Measurement should ship with the prototype so every test feeds the Wisdom Graph.",
                [
                    "Capture route selected, confidence, edits, focus-workspace opens, export actions, and efficacy ratings.",
                    "Add a post-execution rating that stores whether the framework clarified, decided, acted, or stalled.",
                    "Use metrics to improve future routing and framework suggestions.",
                ],
                [
                    "Reach touches every user session.",
                    "Impact is lower than core product features but compounds learning.",
                    "Confidence is high because instrumentation is straightforward.",
                ],
            ),
        ]

    rows = sorted(rows, key=lambda row: row["score"], reverse=True)

    return {
        "type": "score_table",
        "title": "RICE Prioritization Canvas",
        "subtitle": f"Inferred feature ranking for: {topic}",
        "formula": "Reach x Impact x Confidence / Effort",
        "analysis_brief": [
            f"OmniFrame inferred {len(rows)} buildable initiatives from the supplied idea instead of requiring a pre-written feature list.",
            "Scores favor first-month usefulness, evidence creation, cold-start risk reduction, and implementation effort.",
            "Click any initiative to open a focused workspace with generated options you can accept, combine, or edit. Export a PDF when the analysis is ready to share.",
        ],
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
        "analysis_brief": [
            "OmniFrame selected TRIZ because the prompt implies a constraint conflict.",
            "Choose a principle to open a focused workspace with generated moves, prototypes, and failure checks.",
        ],
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
