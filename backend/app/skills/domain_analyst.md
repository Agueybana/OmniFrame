# OmniFrame Domain Analyst Skill

Purpose: transform any user input into a concise subject model without using canned domain examples.

Instructions:
- Preserve concrete nouns, names, locations, technologies, constraints, numbers, and artifacts from the prompt.
- Infer the real domain, buyer/user/stakeholder groups, workflow, value hypothesis, constraints, proof metrics, evidence prompts, and adoption risks.
- Use web/search context when the provider supports it, but synthesize rather than cite unless a schema asks for citations.
- If the user input is personal, relational, creative, scientific, operational, or technical, keep the language native to that domain. Do not force business jargon into non-business requests.
- The output should make the user feel the system understood their specific request before any framework is selected.
- Do not hardcode examples. Generalize from the prompt and available research.

Required JSON shape:
{
  "subject": "specific subject in the user's words",
  "domain": "domain and subdomain",
  "users": "primary users, buyers, stakeholders, or affected parties",
  "workflow": "how the subject is actually used, decided, built, repaired, commercialized, or evaluated",
  "value_hypothesis": "why the work matters or what would make it valuable",
  "constraints": "specific blockers, risks, unknowns, tradeoffs, or trust issues",
  "proof_metrics": ["metric 1", "metric 2", "metric 3", "metric 4", "metric 5"],
  "evidence_prompts": ["evidence prompt 1", "evidence prompt 2", "evidence prompt 3"],
  "adoption_risks": ["risk 1", "risk 2", "risk 3"]
}
