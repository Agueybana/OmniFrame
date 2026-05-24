# OmniFrame Context Accumulator Skill

Purpose: preserve cumulative context as the user opens framework layers, selects suggestions, edits notes, and regenerates options.

Instructions:
- Treat the original prompt as immutable source context.
- Treat selected chips, edited notes, current focus title, current panel title, and current panel value as the newest local context.
- Generate new options from the combination of original prompt plus current layer context.
- Do not repeat options already shown unless the user explicitly asks for a summary.
- Keep each option in the semantic lane of the panel:
  - Evidence panels produce proof, validation, inspection, or research signals.
  - Action panels produce concrete next moves.
  - Metric panels produce observable measurements and thresholds.
  - Risk panels produce failure modes and watch-outs.
  - Experiment panels produce tests with baseline, variation, and decision rule.
  - Definition panels produce requirements, scope boundaries, and acceptance criteria.
  - Contradiction panels produce improve-X-without-worsening-Y formulations.
- Avoid generic placeholders such as "talk to users" unless it names which users, about what, and what proof is expected.
