from backend.app.services.canvas_generators import generate_rice, generate_swot


def test_rice_infers_triangle_event_features():
    canvas = generate_rice(
        "I need to rank features that an app like Triangle Gig & Event Agent would need. "
        "Autonomous agents scrape the web daily to curate RTP arts/music events. "
        "Users find hyper-specific entertainment, artists find open mics and venues. "
        "Cold start problem. Needs enough initial scraped data to be useful to the first 100 users."
    )

    initiatives = [row["initiative"] for row in canvas["rows"]]

    assert len(initiatives) == 6
    assert "Hyperlocal discovery feed with mood, genre, neighborhood, and date filters" in initiatives
    assert "Daily multi-source event ingestion agent" in initiatives
    assert canvas["rows"][0]["drilldown"]["panels"][0]["options"]


def test_swot_uses_project_specific_table_content():
    goal = (
        "Project / Technology\tPurpose\tDetails & Description\tUser Acquisition / Traction Challenges\tKey Benefit / Problem Solved\n"
        "1. Agent-Trust Cert (\"VeriBot\")\tB2B Trust Infrastructure\tA protocol/badge system signaling to visiting LLMs that a store is audited and safe.\t"
        "High educational barrier. Merchants won't care until agents are buying things.\tMerchants capture agent-driven sales.\n"
        "2. VibeOS or SprintZero (AI-Native Jira / Requirements AI)\tEnd-to-End Product Management\tAn OS for vibecoding that automates the requirements workshop.\t"
        "High ambition requires a flawless UX and a two-sided marketplace.\tA single pipeline from raw idea to deployed product.\n"
        "3. Triangle Gig & Event Agent\tLocalized Data Curation\tAutonomous agents scrape the web daily to curate RTP arts/music events.\t"
        "Cold start problem.\tA single source of truth for local culture.\n"
        "4. AutoValidate (Idea Validator)\tGTM / Product Validation\tSpins up a micro-landing page and validation metrics before building.\t"
        "Founders often do not want to pay to find out their idea is bad.\tProves market demand before build.\n"
        "5. Nexus (Cross-Domain DB Agent)\tResearch / Data Mining\tConnects public databases to find novel overlaps.\t"
        "Extremely high compute costs.\tAutomates interdisciplinary discovery."
    )
    canvas = generate_swot(goal)
    rendered = " ".join(item["text"] for section in canvas["sections"] for item in section["items"])

    assert "Triangle Gig & Event Agent" in rendered
    assert "VibeOS or SprintZero" in rendered
    assert "Agent-Trust Cert" in rendered
    assert "Nexus" in rendered
