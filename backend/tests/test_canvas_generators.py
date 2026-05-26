from backend.app.services.canvas_generators import (
    DomainBrief,
    build_canvas,
    generate_from_catalog,
    generate_swot,
    generate_triz,
)


def test_triz_uses_domain_brief_without_example_branches():
    brief = DomainBrief(
        subject="lighter portable field shelter",
        domain="outdoor equipment structural design",
        users="field researchers, disaster-response teams, equipment designers, and materials engineers",
        workflow="change shelter construction while preserving setup speed, wind resistance, durability, and pack weight",
        value_hypothesis="users value lower carry weight only if setup speed, weather resistance, and durability survive field use",
        constraints="lower mass can reduce wind tolerance, joint strength, weather resistance, or repairability",
        proof_metrics=["packed-weight reduction", "wind-load survival", "setup time"],
        evidence_prompts=["Test material coupons and full shelter prototypes."],
        adoption_risks=["A light shelter that fails in weather loses trust."],
    )
    canvas = generate_triz("Build a lighter portable field shelter.", brief)
    rendered = " ".join(canvas["analysis_brief"]) + " " + str(canvas["solution_cards"])

    assert "outdoor equipment structural design" in rendered
    assert "pack weight" in rendered.lower()
    assert canvas["principles"][0]["drilldown"]["panels"] == []


def test_swot_drilldown_panels_keep_distinct_option_domains():
    canvas = generate_swot("Commercialize our route-optimization algorithm for mid-size logistics carriers.")
    item = canvas["sections"][1]["items"][0]
    panels = {panel["title"]: panel for panel in item["drilldown"]["panels"]}

    assert panels["Evidence to verify"]["kind"] == "evidence"
    assert panels["Strategic action"]["kind"] == "action"
    assert panels["Watch metric"]["kind"] == "metric"
    assert "metric" not in " ".join(panels["Strategic action"]["option_sets"][0]).lower()
    assert "next move" not in " ".join(panels["Watch metric"]["option_sets"][0]).lower()


def test_domain_brief_drives_all_live_frameworks_without_hardcoded_examples():
    goal = "commercialize a wetland drone mapping algorithm."
    brief = DomainBrief(
        subject="commercializing a wetland drone mapping algorithm",
        domain="wetland restoration, drone imagery analytics, and environmental monitoring software",
        users="restoration ecologists, conservation nonprofits, state permitting teams, and drone service providers",
        workflow="turn drone imagery into vegetation, hydrology, invasive species, and restoration-progress evidence",
        value_hypothesis="customers pay if the output reduces field survey time and improves grant, compliance, or restoration decisions",
        constraints="imagery quality, seasonal variance, species classification confidence, regulatory trust, and field validation burden",
        proof_metrics=["field survey hours saved", "classification precision", "permit evidence acceptance"],
        evidence_prompts=["Compare model output against field transects."],
        adoption_risks=["Regulators may reject unsupported model claims."],
    )
    for framework_id in ["swot", "lean_startup", "okrs", "porters_five_forces", "pestle", "rice", "triz"]:
        canvas = build_canvas(framework_id, goal, brief)
        rendered = str(canvas)
        assert "wetland" in rendered.lower() or "drone" in rendered.lower()


def test_generate_from_catalog_swot_renders_quadrant_from_catalog():
    canvas = generate_from_catalog("swot", "commercialize a wetland drone mapping algorithm.")

    assert canvas["type"] == "quadrant"
    assert [section["label"] for section in canvas["sections"]] == [
        "Strengths",
        "Weaknesses",
        "Opportunities",
        "Threats",
    ]
    item = canvas["sections"][0]["items"][0]
    assert {"text", "rationale", "metric", "options", "drilldown"} <= set(item)
    assert [panel["title"] for panel in item["drilldown"]["panels"]] == [
        "Evidence to verify",
        "Strategic action",
        "Watch metric",
    ]


def test_generate_from_catalog_board_uses_one_lane_per_component():
    canvas = generate_from_catalog("jtbd", "improve onboarding for our analytics product.")

    assert canvas["type"] == "framework_board"
    assert canvas["title"] == "Jobs To Be Done Canvas"
    assert [lane["label"] for lane in canvas["lanes"]] == [
        "User needs",
        "core tasks",
        "hired/fired products",
    ]
    item = canvas["lanes"][0]["items"][0]
    assert {"title", "body", "metric", "options", "drilldown"} <= set(item)
    assert item["drilldown"]["panels"]


def test_build_canvas_falls_back_to_catalog_for_unregistered_framework():
    goal = "improve onboarding for our analytics product."

    catalog_canvas = build_canvas("jtbd", goal)
    assert catalog_canvas["type"] == "framework_board"
    assert catalog_canvas["title"] == "Jobs To Be Done Canvas"

    # Frameworks with bespoke generators keep using them, not the catalog fallback.
    swot_canvas = build_canvas("swot", goal)
    assert swot_canvas["type"] == "quadrant"
    assert swot_canvas["title"] != "SWOT Canvas"  # generate_from_catalog would title it this


def test_catalog_canvas_does_not_display_component_prompt():
    from backend.app.services.frameworks import get_framework

    goal = "Grow our SaaS analytics product among mid-market teams."
    for framework_id in ["aarrr", "tows"]:  # exercises framework_board and quadrant paths
        framework = get_framework(framework_id)
        rendered = str(generate_from_catalog(framework_id, goal))
        for component in framework["components"]:
            chunk = (component.get("prompt") or "").strip()[:60]
            if chunk:
                assert chunk not in rendered, f"prompt leaked into canvas for {framework_id}/{component['id']}"
        # The short description is what should drive the displayed subheading/body.
        first_description = (framework["components"][0].get("description") or "").strip()[:40]
        if first_description:
            assert first_description in rendered
