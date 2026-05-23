import { ArrowLeft, ArrowRight, Calculator, GitBranch, LayoutGrid, Lightbulb, PencilLine } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

const FRAMEWORK_ICONS = {
  swot: LayoutGrid,
  rice: Calculator,
  triz: Lightbulb
};

export default function CanvasWorkspace({ route }) {
  const [canvas, setCanvas] = useState(route?.canvas ?? null);
  const [subCanvases, setSubCanvases] = useState([]);
  const [subCanvasIndex, setSubCanvasIndex] = useState(-1);

  useEffect(() => {
    setCanvas(route?.canvas ?? null);
    setSubCanvases([]);
    setSubCanvasIndex(-1);
  }, [route]);

  if (!route || !canvas) {
    return (
      <section id="workspace" className="bg-ink px-4 py-16 sm:px-6">
        <div className="mx-auto max-w-7xl">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-moss">Workspace</p>
          <div className="mt-5 grid gap-4 md:grid-cols-3">
            {[
              ["SWOT", "Strategic audit route for internal and external context."],
              ["RICE", "Prioritization route for roadmaps, backlogs, and feature bets."],
              ["TRIZ", "Contradiction route for engineering tradeoffs and invention."]
            ].map(([title, body]) => (
              <div key={title} className="rounded-lg border border-white/10 bg-white/[0.04] p-5">
                <h3 className="text-lg font-semibold text-white">{title}</h3>
                <p className="mt-3 text-sm leading-6 text-white/56">{body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    );
  }

  const Icon = FRAMEWORK_ICONS[route.framework_id] ?? PencilLine;
  const activeSubCanvas = subCanvasIndex >= 0 ? subCanvases[subCanvasIndex] : null;

  function openSubCanvas(nextSubCanvas) {
    setSubCanvases((current) => {
      const retained = current.slice(0, subCanvasIndex + 1);
      const next = [...retained, nextSubCanvas];
      setSubCanvasIndex(next.length - 1);
      return next;
    });
  }

  function goBack() {
    setSubCanvasIndex((current) => Math.max(-1, current - 1));
  }

  function goForward() {
    setSubCanvasIndex((current) => Math.min(subCanvases.length - 1, current + 1));
  }

  return (
    <section id="workspace" className="bg-ink px-4 py-16 sm:px-6">
      <div className="mx-auto max-w-7xl">
        <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-moss">Generated Canvas</p>
            <div className="mt-3 flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-moss text-ink">
                <Icon size={22} />
              </div>
              <div>
                <h2 className="text-3xl font-semibold text-white">{route.framework_name}</h2>
                <p className="mt-1 text-sm text-white/56">{route.rationale}</p>
              </div>
            </div>
          </div>
          <div className="rounded-lg border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white/72">
            Confidence <span className="font-bold text-white">{Math.round(route.confidence * 100)}%</span>
          </div>
        </div>

        <DecisionOverview route={route} />

        <CanvasNavigator
          activeSubCanvas={activeSubCanvas}
          canGoBack={subCanvasIndex > -1}
          canGoForward={subCanvasIndex < subCanvases.length - 1}
          goBack={goBack}
          goForward={goForward}
          returnRoot={() => setSubCanvasIndex(-1)}
        />

        {activeSubCanvas ? (
          <SubCanvasView subCanvas={activeSubCanvas} />
        ) : (
          <>
            {canvas.type === "quadrant" && <QuadrantCanvas canvas={canvas} onChange={setCanvas} onOpenSubCanvas={openSubCanvas} />}
            {canvas.type === "score_table" && <RiceCanvas canvas={canvas} onChange={setCanvas} onOpenSubCanvas={openSubCanvas} />}
            {canvas.type === "contradiction" && <TrizCanvas canvas={canvas} onChange={setCanvas} onOpenSubCanvas={openSubCanvas} />}
          </>
        )}
      </div>
    </section>
  );
}

function DecisionOverview({ route }) {
  const copy = {
    swot: {
      trigger: "Strategic audit signal",
      method: "OmniFrame detected a broad business assessment with internal and external factors, then selected the route that best separates capability, risk, and market context.",
      signals: ["strategy / market language", "internal capability cues", "external opportunity or threat cues"]
    },
    rice: {
      trigger: "Prioritization signal",
      method: "OmniFrame detected roadmap, feature, ranking, effort, or impact language, then selected the route that can score options with a repeatable formula.",
      signals: ["feature or backlog cues", "impact and effort tradeoffs", "need for ranking"]
    },
    triz: {
      trigger: "Contradiction signal",
      method: "OmniFrame detected an engineering tradeoff where improving one property appears to worsen another, then selected the inventive-principles route.",
      signals: ["constraint conflict", "optimization language", "stronger / lighter / faster / cheaper tension"]
    }
  }[route.framework_id];

  return (
    <aside className="mb-6 grid gap-4 rounded-lg border border-white/10 bg-white/[0.045] p-5 lg:grid-cols-[0.9fr_1.1fr]">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-signal">Decision Overview</p>
        <h3 className="mt-2 text-xl font-semibold text-white">{copy.trigger}</h3>
        <p className="mt-3 text-sm leading-6 text-white/64">{copy.method}</p>
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        {copy.signals.map((signal) => (
          <div key={signal} className="rounded-lg border border-white/10 bg-[#07100d] p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/36">Signal</p>
            <p className="mt-2 text-sm font-medium leading-5 text-white">{signal}</p>
          </div>
        ))}
      </div>
    </aside>
  );
}

function CanvasNavigator({ activeSubCanvas, canGoBack, canGoForward, goBack, goForward, returnRoot }) {
  return (
    <div className="mb-6 flex flex-col gap-3 rounded-lg border border-white/10 bg-[#07100d] p-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-2 text-sm text-white/64">
        <GitBranch size={16} className="text-moss" />
        <button type="button" onClick={returnRoot} className={`font-semibold transition ${activeSubCanvas ? "text-white hover:text-moss" : "text-moss"}`}>
          Root canvas
        </button>
        {activeSubCanvas && (
          <>
            <span>/</span>
            <span className="font-semibold text-white">{activeSubCanvas.title}</span>
          </>
        )}
      </div>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={goBack}
          disabled={!canGoBack}
          className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-sm font-semibold text-white transition hover:border-white/25 disabled:cursor-not-allowed disabled:opacity-35"
        >
          <ArrowLeft size={16} />
          Back
        </button>
        <button
          type="button"
          onClick={goForward}
          disabled={!canGoForward}
          className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-sm font-semibold text-white transition hover:border-white/25 disabled:cursor-not-allowed disabled:opacity-35"
        >
          Forward
          <ArrowRight size={16} />
        </button>
      </div>
    </div>
  );
}

function QuadrantCanvas({ canvas, onChange, onOpenSubCanvas }) {
  function updateItem(sectionId, index, value) {
    onChange({
      ...canvas,
      sections: canvas.sections.map((section) =>
        section.id === sectionId
          ? { ...section, items: section.items.map((item, itemIndex) => (itemIndex === index ? value : item)) }
          : section
      )
    });
  }

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {canvas.sections.map((section) => (
        <div key={section.id} className="rounded-lg border border-white/10 bg-white/[0.04] p-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="text-xl font-semibold text-white">{section.label}</h3>
              <p className="mt-2 text-sm text-white/48">{section.prompt}</p>
            </div>
            <button
              type="button"
              onClick={() => onOpenSubCanvas(buildSwotSubCanvas(section))}
              className="shrink-0 rounded-lg border border-moss/35 bg-moss/10 px-3 py-2 text-xs font-bold uppercase tracking-[0.14em] text-moss transition hover:bg-moss hover:text-ink"
            >
              Open Layer
            </button>
          </div>
          <div className="mt-5 space-y-3">
            {section.items.map((item, index) => (
              <textarea
                key={`${section.id}-${index}`}
                value={item}
                onChange={(event) => updateItem(section.id, index, event.target.value)}
                className={fieldClassName}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function RiceCanvas({ canvas, onChange, onOpenSubCanvas }) {
  const rows = useMemo(
    () =>
      canvas.rows.map((row) => ({
        ...row,
        score: Math.round(((Number(row.reach) * Number(row.impact) * (Number(row.confidence) / 100)) / Number(row.effort)) * 10) / 10
      })),
    [canvas.rows]
  );

  function updateRow(index, key, value) {
    onChange({
      ...canvas,
      rows: canvas.rows.map((row, rowIndex) => (rowIndex === index ? { ...row, [key]: value } : row))
    });
  }

  return (
    <div className="overflow-hidden rounded-lg border border-white/10 bg-white/[0.04]">
      <div className="border-b border-white/10 p-5">
        <h3 className="text-xl font-semibold text-white">{canvas.title}</h3>
        <p className="mt-2 text-sm text-white/52">{canvas.formula}</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[850px] text-left text-sm">
          <thead className="bg-white/[0.04] text-xs uppercase tracking-[0.18em] text-white/40">
            <tr>
              {["Initiative", "Reach", "Impact", "Confidence", "Effort", "Score"].map((heading) => (
                <th key={heading} className="px-4 py-3 font-semibold">
                  {heading}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr key={index} className="border-t border-white/10">
                <td className="px-4 py-3">
                  <input
                    value={row.initiative}
                    onChange={(event) => updateRow(index, "initiative", event.target.value)}
                    className={inputClassName}
                  />
                </td>
                {["reach", "impact", "confidence", "effort"].map((key) => (
                  <td key={key} className="px-4 py-3">
                    <input
                      type="number"
                      min="1"
                      value={row[key]}
                      onChange={(event) => updateRow(index, key, Number(event.target.value))}
                      className="w-24 rounded-md border border-white/10 bg-[#07100d] px-3 py-2 text-white caret-moss outline-none transition placeholder:text-white/32 focus:border-moss focus:ring-2 focus:ring-moss/20"
                    />
                  </td>
                ))}
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <span className="text-lg font-bold text-moss">{row.score}</span>
                    <button
                      type="button"
                      onClick={() => onOpenSubCanvas(buildRiceSubCanvas(row))}
                      className="rounded-md border border-moss/35 bg-moss/10 px-2 py-1 text-xs font-bold uppercase tracking-[0.12em] text-moss transition hover:bg-moss hover:text-ink"
                    >
                      Layer
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function TrizCanvas({ canvas, onChange, onOpenSubCanvas }) {
  function updateContradiction(key, value) {
    onChange({ ...canvas, contradiction: { ...canvas.contradiction, [key]: value } });
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[0.85fr_1.15fr]">
      <div className="rounded-lg border border-white/10 bg-white/[0.04] p-5">
        <h3 className="text-xl font-semibold text-white">Contradiction</h3>
        <p className="mt-2 text-sm text-white/48">{canvas.contradiction.prompt}</p>
        {["improving", "worsening"].map((key) => (
          <label key={key} className="mt-5 block">
            <span className="text-xs font-semibold uppercase tracking-[0.18em] text-white/40">{key}</span>
            <textarea
              value={canvas.contradiction[key]}
              onChange={(event) => updateContradiction(key, event.target.value)}
              className={`mt-2 ${fieldClassName}`}
            />
          </label>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {canvas.principles.map((principle) => (
          <button
            key={principle.number}
            type="button"
            onClick={() => onOpenSubCanvas(buildTrizSubCanvas(principle))}
            className="rounded-lg border border-white/10 bg-white/[0.04] p-5 text-left transition hover:border-moss/60 hover:bg-moss/10"
          >
            <p className="text-xs font-bold text-moss">Principle {principle.number}</p>
            <h4 className="mt-2 text-lg font-semibold text-white">{principle.name}</h4>
            <p className="mt-3 text-sm leading-6 text-white/56">{principle.application}</p>
            <p className="mt-4 text-xs font-bold uppercase tracking-[0.16em] text-signal">Open application layer</p>
          </button>
        ))}
      </div>
    </div>
  );
}

const fieldClassName =
  "min-h-20 w-full resize-y rounded-lg border border-white/10 bg-[#07100d] px-4 py-3 text-sm text-white caret-moss outline-none transition placeholder:text-white/32 selection:bg-moss selection:text-ink focus:border-moss focus:ring-2 focus:ring-moss/20";

const inputClassName =
  "w-full rounded-md border border-white/10 bg-[#07100d] px-3 py-2 text-white caret-moss outline-none transition placeholder:text-white/32 focus:border-moss focus:ring-2 focus:ring-moss/20";

function buildSwotSubCanvas(section) {
  return {
    title: `${section.label} Layer`,
    eyebrow: "SWOT sub-canvas",
    description: `Turn ${section.label.toLowerCase()} into evidence, assumptions, actions, and metrics.`,
    panels: [
      ["Evidence", `What proof supports this ${section.label.toLowerCase()} claim?`],
      ["Assumptions", "Which belief would invalidate this if proven false?"],
      ["Action", "What concrete move should this quadrant trigger?"],
      ["Metric", "How will we know this insight improved the strategy?"]
    ]
  };
}

function buildRiceSubCanvas(row) {
  return {
    title: row.initiative,
    eyebrow: "RICE initiative layer",
    description: `Inspect the assumptions behind a score of ${row.score}.`,
    panels: [
      ["Reach Basis", "Which user segment or account pool creates this reach estimate?"],
      ["Impact Proof", "What evidence supports the impact score?"],
      ["Confidence Risk", "What would increase or decrease confidence?"],
      ["Effort Reducer", "What can be scoped down without losing the core outcome?"]
    ]
  };
}

function buildTrizSubCanvas(principle) {
  return {
    title: `Principle ${principle.number}: ${principle.name}`,
    eyebrow: "TRIZ application layer",
    description: principle.application,
    panels: [
      ["Contradiction Rewrite", "State the improvement and the worsening property in one sentence."],
      ["Inventive Move", "How does this principle change timing, structure, parameter, or mediation?"],
      ["Prototype", "What is the smallest experiment that proves the idea works?"],
      ["Failure Mode", "What new weakness might this inventive move create?"]
    ]
  };
}

function SubCanvasView({ subCanvas }) {
  return (
    <div className="rounded-lg border border-moss/25 bg-[#0a120f] p-5 shadow-glow">
      <p className="text-xs font-semibold uppercase tracking-[0.24em] text-moss">{subCanvas.eyebrow}</p>
      <h3 className="mt-3 text-3xl font-semibold text-white">{subCanvas.title}</h3>
      <p className="mt-3 max-w-3xl text-sm leading-6 text-white/60">{subCanvas.description}</p>
      <div className="mt-6 grid gap-4 md:grid-cols-2">
        {subCanvas.panels.map(([title, prompt]) => (
          <label key={title} className="block rounded-lg border border-white/10 bg-white/[0.04] p-4">
            <span className="text-sm font-semibold text-white">{title}</span>
            <p className="mt-2 text-sm leading-6 text-white/48">{prompt}</p>
            <textarea className={`mt-4 ${fieldClassName}`} placeholder="Add notes for this layer..." />
          </label>
        ))}
      </div>
    </div>
  );
}
