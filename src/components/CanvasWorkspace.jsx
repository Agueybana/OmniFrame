import {
  ArrowLeft,
  ArrowRight,
  Calculator,
  Compass,
  Download,
  GitBranch,
  LayoutGrid,
  Lightbulb,
  MousePointerClick,
  PencilLine,
  RefreshCw,
  Sparkles
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { refreshOptions } from "../lib/api";

const FRAMEWORK_ICONS = {
  swot: LayoutGrid,
  lean_startup: Sparkles,
  okrs: Compass,
  porters_five_forces: GitBranch,
  pestle: MousePointerClick,
  rice: Calculator,
  triz: Lightbulb
};

export default function CanvasWorkspace({ route }) {
  const [canvas, setCanvas] = useState(route?.canvas ?? null);
  const [focusCanvases, setFocusCanvases] = useState([]);
  const [focusIndex, setFocusIndex] = useState(-1);

  useEffect(() => {
    setCanvas(route?.canvas ?? null);
    setFocusCanvases([]);
    setFocusIndex(-1);
  }, [route]);

  if (!route || !canvas) {
    return (
      <section id="workspace" className="bg-ink px-4 py-16 sm:px-6">
        <div className="mx-auto max-w-7xl">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-moss">Workspace</p>
          <div className="mt-5 grid gap-4 md:grid-cols-3">
            {[
              ["SWOT", "Strategic audit route for internal and external context."],
              ["Lean Startup", "Experiment route for MVP validation and learning loops."],
              ["OKRs", "Alignment route for objectives, key results, and operating cadence."],
              ["Porter's Five Forces", "Industry structure route for competitive pressure and profit pools."],
              ["PESTLE", "Macro risk route for political, economic, social, technical, legal, and environmental forces."],
              ["RICE", "Prioritization route for roadmaps, backlogs, and feature bets."],
              ["TRIZ", "Contradiction route for engineering tradeoffs and invention."]
            ].map(([title, body]) => (
              <div key={title} className="depth-card rounded-lg border border-white/10 bg-white/[0.04] p-5">
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
  const activeFocus = focusIndex >= 0 ? focusCanvases[focusIndex] : null;

  function openFocus(nextFocus) {
    const preparedFocus = normalizeFocusCanvas(nextFocus);
    setFocusCanvases((current) => {
      const retained = current.slice(0, focusIndex + 1);
      const next = [...retained, preparedFocus];
      setFocusIndex(next.length - 1);
      return next;
    });
  }

  function updateActiveFocus(nextFocus) {
    setFocusCanvases((current) => current.map((item, index) => (index === focusIndex ? nextFocus : item)));
  }

  function goBack() {
    setFocusIndex((current) => Math.max(-1, current - 1));
  }

  function goForward() {
    setFocusIndex((current) => Math.min(focusCanvases.length - 1, current + 1));
  }

  function exportPdf() {
    openReportWindow(route, getReportCanvas(canvas), focusCanvases);
  }

  return (
    <section id="workspace" className="bg-ink px-4 py-16 sm:px-6">
      <div className="mx-auto max-w-7xl">
        <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-moss">Generated Canvas</p>
            <div className="mt-3 flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-moss text-ink shadow-[0_16px_36px_rgba(34,197,94,0.28)]">
                <Icon size={22} />
              </div>
              <div>
                <h2 className="text-3xl font-semibold text-white">{route.framework_name}</h2>
                <p className="mt-1 max-w-3xl text-sm text-white/62">{route.rationale}</p>
              </div>
            </div>
          </div>
          <div className="flex flex-wrap gap-3">
            <button type="button" onClick={exportPdf} className="report-button inline-flex items-center gap-2 rounded-lg px-4 py-3 text-sm font-bold text-ink">
              <Download size={17} />
              Export PDF
            </button>
            <div className="rounded-lg border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white/72">
              Confidence <span className="font-bold text-white">{Math.round(route.confidence * 100)}%</span>
            </div>
          </div>
        </div>

        <DecisionOverview route={route} canvas={canvas} />
        <GuideDock route={route} activeFocus={activeFocus} />

        <CanvasNavigator
          activeFocus={activeFocus}
          canGoBack={focusIndex > -1}
          canGoForward={focusIndex < focusCanvases.length - 1}
          goBack={goBack}
          goForward={goForward}
          returnRoot={() => setFocusIndex(-1)}
        />

        {activeFocus ? (
          <FocusCanvasView focusCanvas={activeFocus} onChange={updateActiveFocus} onExport={exportPdf} route={route} />
        ) : (
          <>
            <PromptPanorama route={route} canvas={canvas} />
            <AnalysisBrief canvas={canvas} />
            {canvas.type === "quadrant" && <QuadrantCanvas canvas={canvas} onChange={setCanvas} onOpenFocus={openFocus} />}
            {canvas.type === "score_table" && <RiceCanvas canvas={canvas} onChange={setCanvas} onOpenFocus={openFocus} />}
            {canvas.type === "contradiction" && <TrizCanvas canvas={canvas} onChange={setCanvas} onOpenFocus={openFocus} />}
            {canvas.type === "framework_board" && <FrameworkBoardCanvas canvas={canvas} onOpenFocus={openFocus} />}
            {canvas.type === "okr_board" && <OkrCanvas canvas={canvas} onOpenFocus={openFocus} />}
            {canvas.type === "force_map" && <ForceMapCanvas canvas={canvas} onOpenFocus={openFocus} />}
          </>
        )}
      </div>
    </section>
  );
}

function PromptPanorama({ route, canvas }) {
  const variables = getCanvasPanorama(canvas);
  const context = canvas.analysis_brief?.[0] || canvas.subtitle || route.rationale;
  const domainBrief = route.selection_process?.domain_brief;

  return (
    <section className="mb-6 rounded-lg border border-moss/20 bg-[#07100d] p-5 shadow-[0_24px_80px_rgba(34,197,94,0.08)]">
      <div className="grid gap-5 lg:grid-cols-[0.95fr_1.05fr]">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-moss">Input panorama</p>
          <h3 className="mt-2 text-2xl font-semibold text-white">Prompt focus and derived context</h3>
          <TypedRevealText className="mt-3 text-sm leading-6 text-white/66" text={compactText(route.goal || "No prompt captured.", 420)} />
          <div className="mt-4 rounded-lg border border-white/10 bg-white/[0.04] p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-white/36">Derived read</p>
            <TypedRevealText className="mt-2 text-sm leading-6 text-white/70" text={context} />
          </div>
          {domainBrief && (
            <div className="mt-4 rounded-lg border border-signal/20 bg-signal/10 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-signal">Agent subject model</p>
              <TypedRevealText className="mt-2 text-sm leading-6 text-white/72" text={`${domainBrief.users}. Workflow: ${domainBrief.workflow}`} />
            </div>
          )}
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-signal">Framework variables</p>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            {variables.map((variable) => (
              <div key={`${variable.label}-${variable.value}`} className="depth-card rounded-lg border border-white/10 bg-white/[0.04] p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-white/36">{variable.label}</p>
                <TypedRevealText className="mt-2 text-sm font-semibold leading-5 text-white" text={variable.value} />
                {variable.detail && <TypedRevealText className="mt-2 text-xs leading-5 text-white/52" text={variable.detail} />}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function AnalysisBrief({ canvas }) {
  if (!canvas.analysis_brief?.length) {
    return null;
  }

  return (
    <div className="mb-6 grid gap-3 lg:grid-cols-3">
      {canvas.analysis_brief.map((brief, index) => (
        <div key={`${brief}-${index}`} className="depth-card rounded-lg border border-white/10 bg-[#07100d] p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-moss">System read {index + 1}</p>
          <TypedRevealText className="mt-2 text-sm leading-6 text-white/70" text={brief} />
        </div>
      ))}
    </div>
  );
}

function TypedRevealText({ text, className = "" }) {
  const ref = useRef(null);
  const fullText = String(text ?? "");
  const [visible, setVisible] = useState(false);
  const [displayed, setDisplayed] = useState("");

  useEffect(() => {
    const node = ref.current;
    if (!node) return undefined;
    const observer = new IntersectionObserver(
      ([entry]) => {
        setVisible(entry.isIntersecting);
        if (!entry.isIntersecting) {
          setDisplayed("");
        }
      },
      { threshold: 0.35, rootMargin: "0px 0px -8% 0px" }
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!visible) return undefined;
    const prefersReducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;
    if (prefersReducedMotion) {
      setDisplayed(fullText);
      return undefined;
    }
    setDisplayed("");
    let index = 0;
    const interval = window.setInterval(() => {
      index += Math.max(1, Math.ceil(fullText.length / 120));
      setDisplayed(fullText.slice(0, index));
      if (index >= fullText.length) {
        window.clearInterval(interval);
      }
    }, 14);
    return () => window.clearInterval(interval);
  }, [fullText, visible]);

  return (
    <p ref={ref} className={`typed-reveal ${className}`}>
      {displayed || (visible ? "" : fullText)}
      {visible && displayed.length < fullText.length && <span className="typed-caret">|</span>}
    </p>
  );
}

function DecisionOverview({ route, canvas }) {
  const isRelationship = /relationship|dating|breakup|partner|girlfriend|boyfriend|wife|husband|family/i.test(`${canvas.title ?? ""} ${route.rationale ?? ""}`);
  const copy = {
    swot: {
      trigger: isRelationship ? "Personal decision signal" : "Strategic audit signal",
      method: isRelationship
        ? "OmniFrame detected a relationship or dating decision, then selected SWOT to separate personal strengths, unclear patterns, opportunities for healthier action, and risks without forcing a premature yes/no answer."
        : "OmniFrame detected a business assessment with internal capabilities, market conditions, competitors, adoption risks, or opportunity language. SWOT was selected because it separates controllable assets from external forces before choosing a build path.",
      signals: isRelationship ? ["personal values and needs", "behavior patterns", "decision risks"] : ["internal capability cues", "external opportunity cues", "competitive and adoption risk"]
    },
    lean_startup: {
      trigger: "Validation signal",
      method:
        "OmniFrame detected MVP, validation, traction, experiment, or uncertainty language. Lean Startup was selected because it turns the idea into a Build-Measure-Learn loop with a falsifiable learning goal.",
      signals: ["MVP or validation cues", "riskiest assumption", "build-measure-learn loop"]
    },
    okrs: {
      trigger: "Alignment signal",
      method:
        "OmniFrame detected goals, objectives, measures, or team alignment language. OKRs were selected because they convert direction into measurable outcomes and review cadence.",
      signals: ["objective language", "measurable outcomes", "team alignment"]
    },
    porters_five_forces: {
      trigger: "Industry structure signal",
      method:
        "OmniFrame detected competition, industry, buyers, suppliers, substitutes, or profitability language. Porter's Five Forces was selected to inspect structural pressure before strategy.",
      signals: ["competitive pressure", "buyer or supplier power", "substitute risk"]
    },
    pestle: {
      trigger: "Macro-environment signal",
      method:
        "OmniFrame detected regulatory, global, legal, economic, political, technological, or environmental forces. PESTLE was selected to separate external tailwinds and headwinds.",
      signals: ["macro forces", "regulatory or legal exposure", "external watch metrics"]
    },
    rice: {
      trigger: "Prioritization signal",
      method:
        "OmniFrame detected roadmap, feature, ranking, effort, impact, or what-to-build language. RICE was selected because it can infer initiatives, score tradeoffs, and expose the assumptions behind each build bet.",
      signals: ["feature or backlog cues", "impact and effort tradeoffs", "need for ranked execution"]
    },
    triz: {
      trigger: "Contradiction signal",
      method:
        "OmniFrame detected a constraint conflict where improving one system property may worsen another. TRIZ was selected because it turns the conflict into inventive principles and prototype moves.",
      signals: ["constraint conflict", "optimization language", "stronger / lighter / faster tension"]
    }
  }[route.framework_id] ?? {
    trigger: "Framework signal",
    method: "OmniFrame selected this route because it best matches the strongest language in the goal.",
    signals: ["goal language", "framework fit", "execution guidance"]
  };
  const selectionProcess = route.selection_process;
  const domainBrief = selectionProcess?.domain_brief;
  const passes = selectionProcess?.passes ?? [];
  const reinforcer = selectionProcess?.reinforcer;
  const subjectMethod = domainBrief
    ? `${route.rationale || copy.method} OmniFrame is treating the work as ${domainBrief.workflow}. The proof burden is: ${domainBrief.value_hypothesis}`
    : copy.method;
  const subjectSignals = domainBrief?.proof_metrics?.length ? domainBrief.proof_metrics.slice(0, 3) : copy.signals;

  return (
    <aside className="mb-6 rounded-lg border border-white/10 bg-white/[0.045] p-5">
      <div className="grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-signal">Decision Overview</p>
        <h3 className="mt-2 text-xl font-semibold text-white">{copy.trigger}</h3>
        <p className="mt-3 text-sm leading-6 text-white/68">{subjectMethod}</p>
        <p className="mt-3 text-xs font-semibold uppercase tracking-[0.16em] text-white/36">{canvas.title}</p>
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        {subjectSignals.map((signal) => (
          <div key={signal} className="depth-card rounded-lg border border-white/10 bg-[#07100d] p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/36">{domainBrief ? "Proof signal" : "Signal"}</p>
            <p className="mt-2 text-sm font-medium leading-5 text-white">{signal}</p>
          </div>
        ))}
      </div>
      </div>
      {selectionProcess && (
        <div className="mt-5 border-t border-white/10 pt-5">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-moss">Selection process</p>
              <p className="mt-2 text-sm leading-6 text-white/66">{selectionProcess.summary}</p>
            </div>
            {selectionProcess.mismatch_resolved && (
              <span className="w-fit rounded-md border border-signal/30 bg-signal/10 px-3 py-2 text-xs font-bold uppercase tracking-[0.12em] text-signal">
                Adjudicated mismatch
              </span>
            )}
          </div>
          <div className="mt-4 grid gap-3 lg:grid-cols-3">
            {passes.map((pass) => (
              <div key={`${pass.name}-${pass.winner}`} className="depth-card rounded-lg border border-white/10 bg-[#07100d] p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-white/36">{pass.name}</p>
                <p className="mt-2 text-lg font-semibold text-white">{pass.winner_name}</p>
                <p className="mt-1 text-xs font-semibold text-moss">Confidence {Math.round((pass.confidence ?? 0) * 100)}%</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {(pass.signals ?? []).slice(0, 3).map((signal) => (
                    <span key={signal} className="rounded-full border border-moss/20 bg-moss/10 px-2 py-1 text-[11px] text-moss">
                      {signal}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
          {reinforcer && (
            <div className="mt-3 rounded-lg border border-white/10 bg-white/[0.035] p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-white/36">LLM reinforcer</p>
              <p className="mt-2 text-sm leading-6 text-white/66">
                {reinforcer.framework_name} {reinforcer.agreement === false ? "challenged" : "confirmed"} the criteria route at {Math.round((reinforcer.confidence ?? 0) * 100)}% confidence. {reinforcer.rationale}
              </p>
            </div>
          )}
        </div>
      )}
    </aside>
  );
}

function GuideDock({ route, activeFocus }) {
  const prompt = activeFocus
    ? "Use the generated buttons to fill a note, then edit it into your own decision. Export PDF when this focus view is decision-ready."
    : {
        swot: "Click a strategic insight to inspect evidence, actions, and metrics. This keeps the SWOT from staying generic.",
        lean_startup: "Open a card to turn the idea into a sharper MVP test, metric, and pivot/persevere rule.",
        okrs: "Open an objective item to connect key results with owners, weekly rhythm, and measurable execution.",
        porters_five_forces: "Open a force to collect evidence, pressure ratings, and structural strategy moves.",
        pestle: "Open a macro factor to classify tailwinds, headwinds, watch signals, and adaptation triggers.",
        rice: "Click an initiative to inspect the score assumptions. Suggested buttons can fill deeper notes without making you start from blank text.",
        triz: "Click a principle to turn the contradiction into an experiment, failure check, and prototype move."
      }[route.framework_id] ?? "Hover and open cards to get specific guidance, deeper options, and report-ready notes.";

  return (
    <div className="floating-suggestion mb-6 flex flex-col gap-3 rounded-lg border border-moss/25 bg-[#09120f] p-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-start gap-3">
        <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-moss/15 text-moss">
          <Sparkles size={18} />
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-moss">Live guidance</p>
          <p className="mt-1 text-sm leading-6 text-white/72">{prompt}</p>
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-2 rounded-md border border-white/10 bg-white/[0.04] px-3 py-2 text-xs font-semibold uppercase tracking-[0.14em] text-white/54">
        <MousePointerClick size={15} className="text-signal" />
        Explore, edit, export
      </div>
    </div>
  );
}

function CanvasNavigator({ activeFocus, canGoBack, canGoForward, goBack, goForward, returnRoot }) {
  return (
    <div className="mb-6 flex flex-col gap-3 rounded-lg border border-white/10 bg-[#07100d] p-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-2 text-sm text-white/64">
        <GitBranch size={16} className="text-moss" />
        <button type="button" onClick={returnRoot} className={`font-semibold transition ${activeFocus ? "text-white hover:text-moss" : "text-moss"}`}>
          Root canvas
        </button>
        {activeFocus && (
          <>
            <span>/</span>
            <span className="font-semibold text-white">{activeFocus.title}</span>
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

function HoverHint({ text, children, placement = "card" }) {
  const [dismissed, setDismissed] = useState(false);
  const [timedOut, setTimedOut] = useState(false);
  const timerRef = useRef(null);
  useEffect(() => () => clearTimeout(timerRef.current), []);

  function startTimer() {
    if (dismissed) return;
    clearTimeout(timerRef.current);
    setTimedOut(false);
    timerRef.current = setTimeout(() => setTimedOut(true), 5000);
  }

  function stopTimer() {
    clearTimeout(timerRef.current);
    setTimedOut(false);
  }

  function dismissHint() {
    clearTimeout(timerRef.current);
    setDismissed(true);
  }

  const className = [
    "hint-target",
    "group",
    "relative",
    placement === "control" ? "hint-target-control" : "hint-target-card",
    dismissed ? "hint-target-dismissed" : "",
    timedOut ? "hint-target-timeout" : ""
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={className}
      onPointerEnter={startTimer}
      onPointerLeave={stopTimer}
      onFocusCapture={dismissHint}
      onPointerDownCapture={(event) => {
        if (!event.target.closest(".hint-bubble")) {
          dismissHint();
        }
      }}
    >
      {children}
      <div
        className="hint-bubble absolute z-20 rounded-lg border border-moss/25 bg-[#07100d] px-3 py-2 text-xs leading-5 text-white/78 opacity-0 shadow-glow transition group-hover:opacity-100"
        onPointerEnter={dismissHint}
      >
        {text}
      </div>
    </div>
  );
}

function QuadrantCanvas({ canvas, onChange, onOpenFocus }) {
  function updateItem(sectionId, index, value) {
    onChange({
      ...canvas,
      sections: canvas.sections.map((section) =>
        section.id === sectionId
          ? {
              ...section,
              items: section.items.map((item, itemIndex) => (itemIndex === index ? updateItemText(item, value) : item))
            }
          : section
      )
    });
  }

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {canvas.sections.map((section) => (
        <div key={section.id} className="depth-card rounded-lg border border-white/10 bg-white/[0.04] p-5">
          <div>
            <h3 className="text-xl font-semibold text-white">{section.label}</h3>
            <p className="mt-2 text-sm text-white/52">{section.prompt}</p>
          </div>
          <div className="mt-5 space-y-3">
            {section.items.map((rawItem, index) => {
              const item = normalizeInsight(rawItem);
              return (
                <HoverHint key={`${section.id}-${index}`} text="Edit the insight directly, or click Explore to open evidence, action, and metric options for this specific item.">
                  <article className="insight-card rounded-lg border border-white/10 bg-[#07100d] p-4">
                    <textarea value={item.text} onChange={(event) => updateItem(section.id, index, event.target.value)} className={fieldClassName} />
                    {item.rationale && <p className="mt-3 text-sm leading-6 text-white/58">{item.rationale}</p>}
                    {item.metric && (
                      <div className="mt-3 rounded-md border border-white/10 bg-white/[0.04] px-3 py-2 text-xs font-semibold uppercase tracking-[0.13em] text-white/54">
                        Metric: <span className="normal-case tracking-normal text-white/78">{item.metric}</span>
                      </div>
                    )}
                    <div className="mt-4 flex flex-wrap items-center gap-2">
                      {(item.options ?? []).slice(0, 2).map((option) => (
                        <span key={option} className="option-preview rounded-full border border-moss/20 bg-moss/10 px-3 py-1 text-xs text-moss">
                          {option}
                        </span>
                      ))}
                      <button
                        type="button"
                        onClick={() => onOpenFocus(buildSwotFocus(section, item))}
                        className="ml-auto inline-flex items-center gap-2 rounded-md border border-moss/35 bg-moss/10 px-3 py-2 text-xs font-bold uppercase tracking-[0.12em] text-moss transition hover:bg-moss hover:text-ink"
                      >
                        Explore
                        <ArrowRight size={14} />
                      </button>
                    </div>
                  </article>
                </HoverHint>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

function RiceCanvas({ canvas, onChange, onOpenFocus }) {
  const rows = useMemo(
    () =>
      canvas.rows.map((row) => ({
        ...row,
        score: Math.round(((Number(row.reach) * Number(row.impact) * (Number(row.confidence) / 100)) / Number(row.effort)) * 10) / 10
      })),
    [canvas.rows]
  );
  const maxScore = Math.max(...rows.map((row) => row.score), 1);

  function updateRow(index, key, value) {
    onChange({
      ...canvas,
      rows: canvas.rows.map((row, rowIndex) => (rowIndex === index ? { ...row, [key]: value } : row))
    });
  }

  return (
    <div className="space-y-4">
      <div className="depth-card overflow-hidden rounded-lg border border-white/10 bg-white/[0.04]">
        <div className="border-b border-white/10 p-5">
          <h3 className="text-xl font-semibold text-white">{canvas.title}</h3>
          <p className="mt-2 text-sm text-white/52">{canvas.formula}</p>
        </div>
        <div className="divide-y divide-white/10">
          {rows.map((row, index) => (
            <article key={`${row.initiative}-${index}`} className="rice-row-grid gap-4 p-5">
              <div className="min-w-0">
                <input value={row.initiative} onChange={(event) => updateRow(index, "initiative", event.target.value)} className={inputClassName} />
                {row.rationale && <p className="mt-3 text-sm leading-6 text-white/62">{row.rationale}</p>}
                <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/10">
                  <div className="score-meter h-full rounded-full" style={{ width: `${Math.max(8, (row.score / maxScore) * 100)}%` }} />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                {[
                  ["reach", "Reach"],
                  ["impact", "Impact"],
                  ["confidence", "Conf."],
                  ["effort", "Effort"]
                ].map(([key, label]) => (
                  <label key={key} className="rounded-md border border-white/10 bg-[#07100d] p-2">
                    <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-white/36">{label}</span>
                    <input
                      type="number"
                      min="1"
                      value={row[key]}
                      onChange={(event) => updateRow(index, key, Number(event.target.value))}
                      className="mt-1 w-full bg-transparent text-lg font-bold text-white caret-moss outline-none"
                    />
                  </label>
                ))}
              </div>
              <div className="flex flex-col justify-between rounded-lg border border-moss/20 bg-moss/10 p-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-moss">Score</p>
                  <p className="mt-1 text-3xl font-bold text-white">{row.score}</p>
                </div>
                <button
                  type="button"
                  onClick={() => onOpenFocus(buildRiceFocus(row))}
                  className="mt-4 inline-flex items-center justify-center gap-2 rounded-md bg-moss px-3 py-2 text-xs font-bold uppercase tracking-[0.12em] text-ink transition hover:bg-signal"
                >
                  Explore
                  <ArrowRight size={14} />
                </button>
              </div>
            </article>
          ))}
        </div>
      </div>
    </div>
  );
}

function TrizCanvas({ canvas, onChange, onOpenFocus }) {
  function updateContradiction(key, value) {
    onChange({ ...canvas, contradiction: { ...canvas.contradiction, [key]: value } });
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[0.85fr_1.15fr]">
      <div className="depth-card rounded-lg border border-white/10 bg-white/[0.04] p-5">
        <h3 className="text-xl font-semibold text-white">Contradiction</h3>
        <p className="mt-2 text-sm text-white/48">{canvas.contradiction.prompt}</p>
        {["improving", "worsening"].map((key) => (
          <label key={key} className="mt-5 block">
            <span className="text-xs font-semibold uppercase tracking-[0.18em] text-white/40">{key}</span>
            <textarea value={canvas.contradiction[key]} onChange={(event) => updateContradiction(key, event.target.value)} className={`mt-2 ${fieldClassName}`} />
          </label>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {canvas.principles.map((principle) => (
          <HoverHint key={principle.number} text="Open this principle for material choices, test plans, and regenerated option sets specific to the original problem.">
            <button
              type="button"
              onClick={() => onOpenFocus(buildTrizFocus(principle))}
              className="depth-card w-full rounded-lg border border-white/10 bg-white/[0.04] p-5 text-left transition hover:border-moss/60 hover:bg-moss/10"
            >
              <p className="text-xs font-bold text-moss">Principle {principle.number}</p>
              <h4 className="mt-2 text-lg font-semibold text-white">{principle.name}</h4>
              <p className="mt-3 text-sm leading-6 text-white/56">{principle.application}</p>
              {principle.why_it_fits && <p className="mt-3 text-sm leading-6 text-signal/80">{principle.why_it_fits}</p>}
              <p className="mt-4 text-xs font-bold uppercase tracking-[0.16em] text-signal">Explore application</p>
            </button>
          </HoverHint>
        ))}
      </div>
    </div>
  );
}

function FrameworkBoardCanvas({ canvas, onOpenFocus }) {
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      {canvas.lanes.map((lane) => (
        <section key={lane.id} className="depth-card rounded-lg border border-white/10 bg-white/[0.04] p-5">
          <h3 className="text-xl font-semibold text-white">{lane.label}</h3>
          <p className="mt-2 text-sm leading-6 text-white/52">{lane.prompt}</p>
          <div className="mt-5 space-y-3">
            {lane.items.map((item) => (
              <HoverHint key={item.title} text="Open this card to get suggested evidence, metrics, and editable report notes.">
                <button
                  type="button"
                  onClick={() => onOpenFocus(buildBoardFocus(canvas.title, lane, item))}
                  className="insight-card w-full rounded-lg border border-white/10 bg-[#07100d] p-4 text-left transition hover:border-moss/60"
                >
                  <h4 className="text-base font-semibold text-white">{item.title}</h4>
                  <p className="mt-2 text-sm leading-6 text-white/58">{item.body}</p>
                  {item.metric && <p className="mt-3 text-xs font-bold uppercase tracking-[0.14em] text-moss">Metric: {item.metric}</p>}
                </button>
              </HoverHint>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

function OkrCanvas({ canvas, onOpenFocus }) {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {canvas.objectives.map((objective) => (
        <section key={objective.objective} className="depth-card rounded-lg border border-white/10 bg-white/[0.04] p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-moss">Objective</p>
          <h3 className="mt-2 text-xl font-semibold text-white">{objective.objective}</h3>
          <p className="mt-2 text-sm leading-6 text-white/52">{objective.rationale}</p>
          <div className="mt-4 space-y-2">
            {objective.key_results.map((kr) => (
              <div key={kr} className="rounded-md border border-white/10 bg-[#07100d] px-3 py-2 text-sm text-white/70">
                {kr}
              </div>
            ))}
          </div>
          <div className="mt-4 space-y-3">
            {objective.items.map((item) => (
              <HoverHint key={item.title} text="Open this initiative to assign evidence, owner behavior, and a measurable OKR review signal.">
                <button
                  type="button"
                  onClick={() => onOpenFocus(buildBoardFocus("OKR focus", { label: objective.objective }, item))}
                  className="insight-card w-full rounded-lg border border-moss/20 bg-moss/10 p-4 text-left transition hover:border-moss/70"
                >
                  <h4 className="font-semibold text-white">{item.title}</h4>
                  <p className="mt-2 text-sm leading-6 text-white/58">{item.body}</p>
                </button>
              </HoverHint>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

function ForceMapCanvas({ canvas, onOpenFocus }) {
  return (
    <div className="grid gap-4 lg:grid-cols-5">
      {canvas.forces.map((force) => (
        <HoverHint key={force.name} text="Open this force to collect concrete evidence and decide whether the pressure is a moat, risk, or strategy constraint.">
          <section className="depth-card h-full rounded-lg border border-white/10 bg-white/[0.04] p-4">
            <div className="flex items-start justify-between gap-3">
              <h3 className="text-lg font-semibold text-white">{force.name}</h3>
              <span className="rounded-md border border-moss/25 bg-moss/10 px-2 py-1 text-xs font-bold text-moss">{force.intensity}</span>
            </div>
            <p className="mt-3 text-sm leading-6 text-white/54">{force.question}</p>
            <p className="mt-3 text-sm leading-6 text-white/70">{force.implication}</p>
            <button
              type="button"
              onClick={() => onOpenFocus(buildBoardFocus("Five Forces focus", { label: force.name }, force.items[0]))}
              className="mt-4 inline-flex items-center gap-2 rounded-md border border-moss/35 bg-moss/10 px-3 py-2 text-xs font-bold uppercase tracking-[0.12em] text-moss transition hover:bg-moss hover:text-ink"
            >
              Explore
              <ArrowRight size={14} />
            </button>
          </section>
        </HoverHint>
      ))}
    </div>
  );
}

function FocusCanvasView({ focusCanvas, onChange, onExport, route }) {
  function setPanelValue(panelIndex, value) {
    onChange({
      ...focusCanvas,
      panels: focusCanvas.panels.map((panel, index) => (index === panelIndex ? { ...panel, value } : panel))
    });
  }

  function appendSuggestion(panelIndex, suggestion) {
    const current = focusCanvas.panels[panelIndex].value ?? "";
    const next = current.trim() ? `${current.trim()}\n\n${suggestion}` : suggestion;
    setPanelValue(panelIndex, next);
  }

  async function regeneratePanelOptions(panelIndex) {
    const panel = focusCanvas.panels[panelIndex];
    const currentIndex = panel.regenIndex ?? 0;
    const optionSets = getRegenerationOptionSets(focusCanvas, panel, route);
    const currentSignature = optionSignature(panel.options ?? []);
    const refreshRound = panel.refreshRound ?? 0;
    const isExhausted = currentIndex >= optionSets.length;
    let nextIndex = currentIndex % optionSets.length;

    if (isExhausted) {
      try {
        const refreshed = await refreshOptions({
          goal: route.goal || focusCanvas.description || focusCanvas.title,
          framework_id: route.framework_id,
          focus_title: focusCanvas.title,
          focus_description: focusCanvas.description,
          panel_title: panel.title,
          panel_prompt: panel.prompt,
          panel_kind: panel.kind || getPanelKind(panel),
          panel_value: panel.value,
          refresh_round: refreshRound,
          existing_options: flattenOptionSets([...(panel.option_sets ?? []), panel.options ?? []])
        });
        let mergedOptionSets = mergeOptionSets(panel.option_sets ?? [], refreshed.option_sets ?? []);
        const syntheticSet = buildSyntheticOptionSet(focusCanvas, panel, refreshRound, route);
        mergedOptionSets = mergeOptionSets(mergedOptionSets, [syntheticSet]);
        const nextSet = findFirstFreshSet(mergedOptionSets, currentSignature, optionSets.length) ?? syntheticSet;
        const nextSetIndex = Math.max(0, mergedOptionSets.findIndex((set) => optionSignature(set) === optionSignature(nextSet)));
        onChange({
          ...focusCanvas,
          panels: focusCanvas.panels.map((item, index) =>
            index === panelIndex
              ? {
                  ...item,
                  options: nextSet,
                  option_sets: mergedOptionSets,
                  regenIndex: nextSetIndex + 1,
                  refreshRound: refreshRound + 1
                }
              : item
          )
        });
        return;
      } catch {
        const syntheticSet = buildSyntheticOptionSet(focusCanvas, panel, refreshRound, route);
        const mergedOptionSets = mergeOptionSets(panel.option_sets ?? [], optionSets, [syntheticSet]);
        onChange({
          ...focusCanvas,
          panels: focusCanvas.panels.map((item, index) =>
            index === panelIndex
              ? {
                  ...item,
                  options: syntheticSet,
                  option_sets: mergedOptionSets,
                  regenIndex: mergedOptionSets.length,
                  refreshRound: refreshRound + 1
                }
              : item
          )
        });
        return;
      }
    }

    for (let attempts = 0; attempts < optionSets.length; attempts += 1) {
      const candidateIndex = (currentIndex + attempts) % optionSets.length;
      if (optionSignature(optionSets[candidateIndex]) !== currentSignature || optionSets.length === 1) {
        nextIndex = candidateIndex;
        break;
      }
    }

    onChange({
      ...focusCanvas,
      panels: focusCanvas.panels.map((item, index) =>
        index === panelIndex ? { ...item, options: optionSets[nextIndex], regenIndex: nextIndex + 1 } : item
      )
    });
  }

  return (
    <div className="focus-stage rounded-lg border border-moss/25 bg-[#0a120f] p-5 shadow-glow">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-moss">{focusCanvas.eyebrow}</p>
          <h3 className="mt-3 text-3xl font-semibold text-white">{focusCanvas.title}</h3>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-white/66">{focusCanvas.description}</p>
        </div>
        <button type="button" onClick={onExport} className="report-button inline-flex shrink-0 items-center justify-center gap-2 rounded-lg px-4 py-3 text-sm font-bold text-ink">
          <Download size={17} />
          Export PDF
        </button>
      </div>
      <div className="mt-6 grid gap-4 md:grid-cols-2">
        {focusCanvas.panels.map((panel, panelIndex) => (
          <section key={`${panel.title}-${panelIndex}`} className="depth-card rounded-lg border border-white/10 bg-white/[0.04] p-4">
            <div className="flex items-start gap-3">
              <HoverHint placement="control" text="Regenerate this section's options using the current focused workspace and notes you have already selected.">
                <button
                  type="button"
                  onClick={() => regeneratePanelOptions(panelIndex)}
                  className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-moss/15 text-moss transition hover:bg-moss hover:text-ink"
                  aria-label={`Regenerate ${panel.title} options`}
                >
                  <RefreshCw size={15} />
                </button>
              </HoverHint>
              <div>
                <h4 className="text-sm font-semibold text-white">{panel.title}</h4>
                <p className="mt-2 text-sm leading-6 text-white/52">{panel.prompt}</p>
              </div>
            </div>
            {panel.options?.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2">
                {panel.options.map((option) => (
                  <button key={option} type="button" onClick={() => appendSuggestion(panelIndex, option)} className="option-chip rounded-full px-3 py-2 text-left text-xs font-medium">
                    {option}
                  </button>
                ))}
              </div>
            )}
            <textarea
              className={`mt-4 ${fieldClassName}`}
              value={panel.value ?? ""}
              onChange={(event) => setPanelValue(panelIndex, event.target.value)}
              placeholder="Click a suggestion or type your own note..."
            />
          </section>
        ))}
      </div>
    </div>
  );
}

const fieldClassName =
  "min-h-24 w-full resize-y rounded-lg border border-white/10 bg-[#07100d] px-4 py-3 text-sm text-white caret-moss outline-none transition placeholder:text-white/32 selection:bg-moss selection:text-ink focus:border-moss focus:ring-2 focus:ring-moss/20";

const inputClassName =
  "w-full rounded-md border border-white/10 bg-[#07100d] px-3 py-2 text-white caret-moss outline-none transition placeholder:text-white/32 focus:border-moss focus:ring-2 focus:ring-moss/20";

function normalizeInsight(item) {
  return typeof item === "string" ? { text: item, options: [] } : item;
}

function updateItemText(item, text) {
  return typeof item === "string" ? text : { ...item, text };
}

function normalizeFocusCanvas(focusCanvas) {
  return {
    ...focusCanvas,
    panels: focusCanvas.panels.map((panel) => ({
      ...panel,
      options: panel.options ?? [],
      option_sets: panel.option_sets ?? [],
      kind: panel.kind ?? getPanelKind(panel),
      refreshRound: panel.refreshRound ?? 0,
      value: panel.value ?? ""
    }))
  };
}

function buildSwotFocus(section, item) {
  const panels =
    item.drilldown?.panels ??
    [
      {
        title: "Evidence to verify",
        prompt: `What proof supports this ${section.label.toLowerCase()} claim?`,
        options: item.options ?? [],
        value: item.options?.[0] ?? ""
      },
      {
        title: "Strategic action",
        prompt: "What concrete move should this trigger?",
        options: ["Create a one-week validation sprint.", "Assign an owner and decision deadline.", "Convert this into a stakeholder-ready report section."]
      },
      {
        title: "Watch metric",
        prompt: "How will you know the insight changed the strategy?",
        options: [item.metric, "Evidence quality score", "Decision confidence delta"].filter(Boolean)
      }
    ];

  return {
    title: `${section.label}: ${item.text.slice(0, 78)}${item.text.length > 78 ? "..." : ""}`,
    eyebrow: "Focused SWOT workspace",
    description: item.drilldown?.description ?? "Turn this strategic observation into evidence, assumptions, actions, and metrics.",
    panels
  };
}

function buildRiceFocus(row) {
  return {
    title: row.initiative,
    eyebrow: "Focused RICE workspace",
    description: row.drilldown?.description ?? `Inspect the assumptions behind a score of ${row.score}.`,
    panels:
      row.drilldown?.panels ??
      [
        { title: "Feature definition", prompt: "Use or edit a tighter requirement.", options: row.options ?? [], value: row.options?.[0] ?? "" },
        { title: "Reach evidence", prompt: "Choose what should justify the reach estimate.", options: row.evidence ?? [] },
        {
          title: "Risk reducer",
          prompt: "Pick a way to increase confidence or reduce effort.",
          options: ["Run a concierge version.", "Instrument the first user action.", "Cut nonessential UI."]
        }
      ]
  };
}

function buildBoardFocus(canvasTitle, lane, item) {
  return {
    title: item.title,
    eyebrow: `${lane.label} workspace`,
    description: item.drilldown?.description ?? `${canvasTitle}: deepen this item into evidence, decisions, and metrics.`,
    panels:
      item.drilldown?.panels ??
      [
        { title: "Best next move", prompt: "Choose or edit the next concrete move.", options: item.options ?? [], value: item.options?.[0] ?? "" },
        { title: "Evidence needed", prompt: "Choose the proof that makes this credible.", options: [`Interview users about ${item.title}`, "Collect one disconfirming data point."] },
        { title: "Decision metric", prompt: "Choose the metric that decides whether this stays in the plan.", options: [item.metric, "Decision confidence improvement"].filter(Boolean) }
      ]
  };
}

function buildTrizFocus(principle) {
  return {
    title: `Principle ${principle.number}: ${principle.name}`,
    eyebrow: "Focused TRIZ workspace",
    description: principle.why_it_fits || principle.application,
    panels:
      principle.drilldown?.panels?.length > 0
        ? principle.drilldown.panels
        : [
            {
              title: "Contradiction rewrite",
              prompt: "State the improvement and worsening property in one sentence.",
              options: ["We need to improve the target property without increasing cost, fragility, or complexity."]
            },
            {
              title: "Inventive move",
              prompt: "How does this principle change timing, structure, parameter, or mediation?",
              options: [principle.application, "Split the system into a fast visible layer and a slower verification layer.", "Move expensive preparation before the user-facing moment."]
            },
            {
              title: "Prototype",
              prompt: "What is the smallest experiment that proves the idea works?",
              options: ["Build a thin demo that simulates the hard part manually.", "Test one measurable contradiction outcome in a 48-hour prototype."]
            },
            {
              title: "Failure mode",
              prompt: "What new weakness might this inventive move create?",
              options: ["The solution may move complexity into operations.", "The mediation layer may reduce speed if it is not instrumented."]
            }
          ]
  };
}

function buildFallbackOptionSets(focusCanvas, panel, route) {
  const subject = compactText([focusCanvas.title, focusCanvas.description, panel.value].filter(Boolean).join(" "), 150);
  const kind = panel.kind ?? getPanelKind(panel);
  const domainBrief = route?.selection_process?.domain_brief;
  const domainSubject = compactText(domainBrief?.subject || subject, 150);
  const domainUsers = compactText(domainBrief?.users || "the most relevant stakeholders", 180);
  const domainWorkflow = compactText(domainBrief?.workflow || subject, 220);
  const domainValue = compactText(domainBrief?.value_hypothesis || "the next action creates decision-grade evidence", 220);
  const domainConstraints = compactText(domainBrief?.constraints || "unclear evidence, weak ownership, and premature scope expansion", 220);
  const domainMetrics = domainBrief?.proof_metrics?.length
    ? domainBrief.proof_metrics.slice(0, 5)
    : ["Decision confidence delta", "Evidence gathered per week", "Time to next concrete action"];
  const templates = {
    evidence: [
      [
        `Collect one direct observation that supports or weakens: ${subject}.`,
        "Ask relevant people for examples rather than opinions.",
        "Separate firsthand evidence from assumptions, hopes, or inherited advice."
      ],
      [
        "Name what evidence would make you reverse this belief.",
        "Look for one counterexample before treating the claim as settled.",
        "Compare the claim against a past pattern, logged behavior, or external data point."
      ]
    ],
    action: [
      [
        `Turn this into one reversible next move tied to: ${subject}.`,
        "Set a clear owner, date, and smallest visible output.",
        "Choose the lowest-drama step that creates new information quickly."
      ],
      [
        "Convert the insight into a short conversation, prototype, or decision memo.",
        "Decide what should stop while this move is tested.",
        "Write the trigger that tells you to continue, revise, or abandon the move."
      ]
    ],
    metric: [
      [
        `Observable change connected to: ${subject}.`,
        "Decision confidence before versus after the next action.",
        "Number of concrete signals collected, reviewed, and acted on."
      ],
      [
        "A pass/fail threshold written before the next experiment starts.",
        "Frequency of the desired behavior or outcome over the next review window.",
        "Time from insight to decision-ready evidence."
      ]
    ],
    risk: [
      [
        `The plan may fail if the core assumption behind '${subject}' is false.`,
        "The next action could produce noise instead of decision-grade evidence.",
        "The work may reduce one risk while quietly increasing another."
      ],
      [
        "A short-term improvement could hide a deeper incompatibility or constraint.",
        "The process may become performative if no decision threshold is set.",
        "The wrong stakeholder or signal could dominate the conclusion."
      ]
    ],
    experiment: [
      [
        `Run a small test that isolates the assumption inside: ${subject}.`,
        "Define baseline, test variant, review date, and stop condition.",
        "Use a manual version first if automation or commitment would be premature."
      ],
      [
        "Choose a 7-day version that creates evidence without locking in the final path.",
        "Record what would count as a pass, a partial pass, and a clear fail.",
        "Keep the experiment narrow enough that one result actually means something."
      ]
    ],
    contradiction: [
      [
        `I want to improve '${subject}' without worsening the most important constraint.`,
        "Name the property that must improve and the property that cannot be sacrificed.",
        "Rewrite the conflict as a single sentence with both sides visible."
      ],
      [
        "Separate the visible symptom from the underlying tradeoff.",
        "State what gets better, what gets worse, and why the current approach couples them.",
        "Define the contradiction so a prototype can test it rather than debate it."
      ]
    ],
    definition: [
      [
        `Rewrite '${subject}' as a concrete requirement with user, trigger, behavior, and outcome.`,
        "Cut wording that does not change the build, decision, or test.",
        "Name the smallest version that still proves the core value."
      ],
      [
        "Describe who uses it, what they do, and how success is visible.",
        "Separate required behavior from polish, automation, or nice-to-have scope.",
        "Add one explicit non-goal so scope does not expand silently."
      ]
    ]
  };

  if (domainBrief) {
    const domainTemplates = {
      evidence: [
        [
          `Verify '${domainSubject}' with direct evidence from ${domainUsers}.`,
          `Inspect the real workflow: ${domainWorkflow}.`,
          `Ask what proof would make users trust or reject this claim: ${subject}.`
        ],
        [
          `Collect a before/after example tied to '${domainValue}'.`,
          `Find one counterexample where '${domainSubject}' would fail despite sounding useful.`,
          `Log source, date, confidence, and decision impact for every signal about ${domainSubject}.`
        ]
      ],
      action: [
        [
          `Turn this panel into one reversible move for '${domainSubject}'.`,
          `Design the move around the actual workflow: ${domainWorkflow}.`,
          `Set the next action so it tests the value hypothesis: ${domainValue}.`
        ],
        [
          `Pick one user group from ${domainUsers} and create a narrow outreach, pilot, or conversation for them.`,
          `Write the decision rule before taking action so the result cannot be rationalized later.`,
          `Stop or defer anything that does not reduce uncertainty about: ${subject}.`
        ]
      ],
      metric: [
        domainMetrics.slice(0, 3),
        [
          `Confidence change for '${domainSubject}' after this panel is tested.`,
          `Number of assumptions converted into pass, fail, or still-unknown status.`,
          `Time from selected option to decision-ready evidence for ${domainSubject}.`
        ]
      ],
      risk: [
        [
          `This may fail if the constraint is underestimated: ${domainConstraints}.`,
          `The option may optimize the wrong part of the workflow: ${domainWorkflow}.`,
          `A good-looking signal may not prove the value hypothesis: ${domainValue}.`
        ],
        [
          `The wrong stakeholder group may dominate the conclusion instead of ${domainUsers}.`,
          `The team may overgeneralize from one case before testing the hardest constraint.`,
          `The action may create activity without changing a real decision.`
        ]
      ],
      experiment: [
        [
          `Run a small test of '${domainSubject}' with baseline, variant, review date, and stop condition.`,
          `Use the real workflow as the test path: ${domainWorkflow}.`,
          `Record whether the result supports the value hypothesis: ${domainValue}.`
        ],
        [
          `Test the hardest constraint first: ${domainConstraints}.`,
          `Use one user segment from ${domainUsers} so the signal is interpretable.`,
          `Define pass, partial-pass, and fail before the test starts.`
        ]
      ],
      contradiction: [
        [
          `Improve '${domainSubject}' without worsening the main constraint: ${domainConstraints}.`,
          `Name what gets better in the workflow and what must not get worse: ${domainWorkflow}.`,
          `Rewrite the conflict as a testable tradeoff rather than a broad aspiration.`
        ],
        [
          `Separate the visible symptom from the underlying coupling in ${domainSubject}.`,
          `Choose a principle that changes timing, structure, mediation, or parameters in the workflow.`,
          `State what proof would show the contradiction has been reduced.`
        ]
      ],
      definition: [
        [
          `Define '${domainSubject}' as user, input, transformation, output, and proof metric.`,
          `Keep the definition anchored to this workflow: ${domainWorkflow}.`,
          `Add one non-goal that protects against scope creep.`
        ],
        [
          `Describe who uses it from ${domainUsers}, what they do, and how success becomes visible.`,
          `Separate must-have behavior from polish, automation, or adjacent features.`,
          `Make the acceptance condition measurable with: ${domainMetrics[0]}.`
        ]
      ]
    };
    return mergeOptionSets(domainTemplates[kind] ?? domainTemplates.action, templates[kind] ?? templates.action);
  }

  return templates[kind] ?? templates.action;
}

function getRegenerationOptionSets(focusCanvas, panel, route) {
  return mergeOptionSets(panel.option_sets ?? [], buildFallbackOptionSets(focusCanvas, panel, route));
}

function mergeOptionSets(...groups) {
  const allSets = groups
    .flat()
    .map((set) => (Array.isArray(set) ? set.filter(Boolean) : []))
    .filter((set) => set.length > 0);
  const seen = new Set();
  const uniqueSets = [];
  for (const set of allSets) {
    const signature = optionSignature(set);
    if (!seen.has(signature)) {
      seen.add(signature);
      uniqueSets.push(set);
    }
  }
  return uniqueSets.length > 0 ? uniqueSets : [["Add a more specific option.", "Add an evidence requirement.", "Add a failure mode."]];
}

function findFirstFreshSet(optionSets, currentSignature, preferredStart = 0) {
  if (!optionSets.length) {
    return null;
  }
  for (let offset = 0; offset < optionSets.length; offset += 1) {
    const candidate = optionSets[(preferredStart + offset) % optionSets.length];
    if (optionSignature(candidate) !== currentSignature) {
      return candidate;
    }
  }
  return optionSets[0];
}

function buildSyntheticOptionSet(focusCanvas, panel, round = 0, route) {
  const subject = compactText([focusCanvas.title, panel.value, focusCanvas.description].filter(Boolean).join(" "), 130);
  const kind = panel.kind ?? getPanelKind(panel);
  const suffix = round > 0 ? ` Refresh ${round + 1}.` : "";
  const domainBrief = route?.selection_process?.domain_brief;
  if (domainBrief) {
    const domainSubject = compactText(domainBrief.subject, 130);
    const domainWorkflow = compactText(domainBrief.workflow, 190);
    const domainUsers = compactText(domainBrief.users, 170);
    const domainValue = compactText(domainBrief.value_hypothesis, 190);
    const domainConstraints = compactText(domainBrief.constraints, 190);
    const metrics = domainBrief.proof_metrics?.length ? domainBrief.proof_metrics : ["decision confidence delta", "evidence gathered per week", "time to next concrete action"];
    const domainVariants = {
      evidence: [
        `Collect a new proof point for '${domainSubject}' from ${domainUsers}.${suffix}`,
        `Compare the claim against the real workflow: ${domainWorkflow}.`,
        `Write the evidence that would weaken this panel's claim about '${subject}'.`
      ],
      action: [
        `Choose one new reversible move for '${domainSubject}' that tests: ${domainValue}.${suffix}`,
        `Make the move visible inside the real workflow: ${domainWorkflow}.`,
        `Define the immediate follow-up if the action produces a clear yes, no, or mixed signal.`
      ],
      metric: [
        `${metrics[round % metrics.length]}.${suffix}`.replace("..", "."),
        `Confidence change after testing '${domainSubject}'.`,
        `Time from selected option to usable evidence in the workflow.`
      ],
      risk: [
        `Name a fresh failure mode from this constraint set: ${domainConstraints}.${suffix}`,
        `Identify the cost of choosing this option too early for '${domainSubject}'.`,
        `State which signal would show the option is creating false confidence.`
      ],
      experiment: [
        `Run a narrow test of '${domainSubject}' using the workflow: ${domainWorkflow}.${suffix}`,
        `Use one user segment from ${domainUsers} so the result explains the next decision.`,
        `Write the pass, partial-pass, and fail rule before the test starts.`
      ],
      contradiction: [
        `Improve '${domainSubject}' without worsening: ${domainConstraints}.${suffix}`,
        `Name the hidden coupling that makes the tradeoff feel unavoidable.`,
        `Choose a small test that separates the two sides by timing, structure, rule, or context.`
      ],
      definition: [
        `Define '${domainSubject}' as actor, trigger, input, transformation, and outcome.${suffix}`,
        `Keep the definition anchored to the workflow: ${domainWorkflow}.`,
        `Add one non-goal to keep the option from expanding into adjacent work.`
      ]
    };
    return domainVariants[kind] ?? domainVariants.action;
  }
  const variants = {
    evidence: [
      `Collect a fresh proof point for '${subject}' and label it confirm, weaken, or unknown.${suffix}`,
      "Ask one new source for a concrete example, then compare it with the strongest existing signal.",
      "Write the evidence that would make this option no longer worth selecting."
    ],
    action: [
      `Select one new reversible action for '${subject}' with a deadline before the next review.${suffix}`,
      "Convert the option into a concrete ask, prototype, outreach, or conversation.",
      "Define the immediate follow-up if the action produces a clear yes, no, or mixed signal."
    ],
    metric: [
      `Track one observable movement for '${subject}' over the next review window.${suffix}`,
      "Record confidence before and after the next selected option is tested.",
      "Count how many assumptions move into pass, fail, or still-unknown status."
    ],
    risk: [
      `Name the newest failure mode that could make '${subject}' misleading.${suffix}`,
      "Identify the cost of choosing this option too early.",
      "State which signal would show the option is creating false confidence."
    ],
    experiment: [
      `Run a small, reversible test for '${subject}' with a baseline and stop condition.${suffix}`,
      "Use one test variant only so the result explains the next decision.",
      "Write the pass, partial-pass, and fail rule before the test starts."
    ],
    contradiction: [
      `Rewrite '${subject}' as improve X without sacrificing Y.${suffix}`,
      "Name the hidden coupling that makes the tradeoff feel unavoidable.",
      "Choose a small test that separates the two sides by timing, structure, rule, or context."
    ],
    definition: [
      `Define '${subject}' as actor, trigger, behavior, and outcome.${suffix}`,
      "Replace broad adjectives with observable behavior or measurable thresholds.",
      "Add one non-goal to keep the option from expanding into adjacent work."
    ]
  };
  return variants[kind] ?? variants.action;
}

function optionSignature(options) {
  return options.map((option) => String(option).trim().toLowerCase()).join("||");
}

function flattenOptionSets(optionSets) {
  return optionSets.flatMap((set) => (Array.isArray(set) ? set : [set])).filter(Boolean);
}

function getPanelKind(panel) {
  const text = `${panel.title ?? ""} ${panel.prompt ?? ""}`.toLowerCase();
  if (/evidence|proof|verify|validate|reach/.test(text)) return "evidence";
  if (/metric|signal|measure|acceptance|score/.test(text)) return "metric";
  if (/risk|failure|threat|obstacle|reducer/.test(text)) return "risk";
  if (/prototype|experiment|mvp|test/.test(text)) return "experiment";
  if (/contradiction/.test(text)) return "contradiction";
  if (/feature|definition|requirement/.test(text)) return "definition";
  return "action";
}

function getCanvasPanorama(canvas) {
  if (canvas.type === "quadrant") {
    return (canvas.sections ?? []).slice(0, 4).map((section) => {
      const first = normalizeInsight(section.items?.[0] ?? {});
      return {
        label: section.label,
        value: first.text || section.prompt,
        detail: first.metric || first.rationale || section.prompt
      };
    });
  }

  if (canvas.type === "score_table") {
    return (canvas.rows ?? []).slice(0, 4).map((row) => ({
      label: `Score ${riceScore(row)}`,
      value: row.initiative,
      detail: row.rationale || `Reach ${row.reach}, impact ${row.impact}, confidence ${row.confidence}%, effort ${row.effort}`
    }));
  }

  if (canvas.type === "contradiction") {
    const contradiction = canvas.contradiction ?? {};
    return [
      { label: "Improving", value: contradiction.improving || "Property to improve", detail: contradiction.prompt },
      { label: "Worsening", value: contradiction.worsening || "Constraint to protect", detail: "TRIZ separates the two sides before selecting principles." },
      ...(canvas.principles ?? []).slice(0, 4).map((principle) => ({
        label: `Principle ${principle.number}`,
        value: principle.name,
        detail: principle.application
      }))
    ];
  }

  if (canvas.type === "framework_board") {
    return (canvas.lanes ?? []).flatMap((lane) =>
      (lane.items ?? []).slice(0, 2).map((item) => ({
        label: lane.label,
        value: item.title,
        detail: item.body || item.metric
      }))
    ).slice(0, 6);
  }

  if (canvas.type === "okr_board") {
    return (canvas.objectives ?? []).slice(0, 4).map((objective) => ({
      label: "Objective",
      value: objective.objective,
      detail: objective.key_results?.slice(0, 2).join(" | ") || objective.rationale
    }));
  }

  if (canvas.type === "force_map") {
    return (canvas.forces ?? []).slice(0, 5).map((force) => ({
      label: force.name,
      value: `${force.intensity} pressure`,
      detail: force.implication || force.question
    }));
  }

  return [{ label: "Canvas", value: canvas.title || "Generated framework", detail: canvas.subtitle || "Open a card for deeper analysis." }];
}

function compactText(value, limit = 160) {
  const cleaned = String(value ?? "").replace(/\s+/g, " ").trim();
  return cleaned.length > limit ? `${cleaned.slice(0, limit - 1).trim()}...` : cleaned;
}

function riceScore(row) {
  const effort = Math.max(Number(row.effort) || 1, 1);
  return Math.round(((Number(row.reach) || 0) * (Number(row.impact) || 0) * ((Number(row.confidence) || 0) / 100) / effort) * 10) / 10;
}

function getReportCanvas(canvas) {
  if (canvas.type !== "score_table") {
    return canvas;
  }
  return {
    ...canvas,
    rows: canvas.rows.map((row) => ({ ...row, score: riceScore(row) }))
  };
}

function openReportWindow(route, canvas, focusCanvases) {
  if (window.pendo?.track) {
    window.pendo.track("omniframe_pdf_export_requested", {
      framework_id: route.framework_id,
      focus_views: focusCanvases.length
    });
  }

  const reportWindow = window.open("", "_blank");
  if (!reportWindow) {
    window.alert("Pop-up blocking prevented the report preview. Allow pop-ups, then use Export PDF again.");
    return;
  }

  reportWindow.document.write(buildReportHtml(route, canvas, focusCanvases));
  reportWindow.document.close();
  reportWindow.focus();
  setTimeout(() => reportWindow.print(), 350);
}

function buildReportHtml(route, canvas, focusCanvases) {
  return `<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>OmniFrame ${escapeHtml(route.framework_name)} Report</title>
  <style>
    body { margin: 0; background: #f6f8f5; color: #0d1110; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    main { max-width: 1040px; margin: 0 auto; padding: 44px; }
    header { background: #0d1110; color: white; border-radius: 22px; padding: 34px; }
    .eyebrow { color: #22c55e; font-size: 11px; font-weight: 800; letter-spacing: .18em; text-transform: uppercase; }
    h1 { margin: 8px 0 10px; font-size: 38px; line-height: 1.05; }
    h2 { margin: 30px 0 12px; font-size: 22px; }
    h3 { margin: 0 0 8px; font-size: 17px; }
    p { line-height: 1.55; }
    .grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
    .card { background: white; border: 1px solid #dbe3dc; border-radius: 16px; padding: 18px; box-shadow: 0 18px 50px rgba(10, 20, 16, .08); page-break-inside: avoid; }
    .muted { color: #4f5f57; }
    .tag { display: inline-block; margin: 4px 4px 0 0; padding: 5px 8px; border-radius: 999px; background: #e8f8ee; color: #137a39; font-size: 11px; font-weight: 700; }
    table { width: 100%; border-collapse: collapse; background: white; border-radius: 16px; overflow: hidden; }
    th, td { padding: 12px; border-bottom: 1px solid #e1e7e2; text-align: left; vertical-align: top; }
    th { background: #0d1110; color: white; font-size: 11px; letter-spacing: .12em; text-transform: uppercase; }
    .bar { height: 7px; background: #dfe7e1; border-radius: 999px; overflow: hidden; margin-top: 8px; }
    .fill { height: 100%; background: linear-gradient(90deg, #22c55e, #80d4ff); }
    @media print { main { padding: 24px; } header, .card { box-shadow: none; } }
  </style>
</head>
<body>
  <main>
    <header>
      <div class="eyebrow">OmniFrame decision report</div>
      <h1>${escapeHtml(route.framework_name)}</h1>
      <p>${escapeHtml(route.rationale)}</p>
      <p>Confidence: <strong>${Math.round(route.confidence * 100)}%</strong></p>
    </header>
    ${renderReportRouteAudit(route)}
    ${renderReportBrief(canvas)}
    ${renderReportCanvas(canvas)}
    ${renderReportFocus(focusCanvases)}
  </main>
</body>
</html>`;
}

function renderReportRouteAudit(route) {
  const process = route.selection_process;
  if (!process) {
    return `<h2>User Prompt</h2><section class="card"><p>${escapeHtml(route.goal ?? "")}</p></section>`;
  }

  return `<h2>Selection Process</h2><section class="card"><p><strong>User prompt:</strong> ${escapeHtml(route.goal ?? "")}</p><p class="muted">${escapeHtml(
    process.summary
  )}</p>${(process.passes ?? [])
    .map(
      (pass) =>
        `<p><strong>${escapeHtml(pass.name)}:</strong> ${escapeHtml(pass.winner_name)} (${Math.round(
          (Number(pass.confidence) || 0) * 100
        )}% confidence) ${escapeHtml((pass.signals ?? []).slice(0, 3).join("; "))}</p>`
    )
    .join("")}${
    process.reinforcer
      ? `<p><strong>LLM reinforcer:</strong> ${escapeHtml(process.reinforcer.framework_name)} at ${Math.round(
          (Number(process.reinforcer.confidence) || 0) * 100
        )}% confidence. ${escapeHtml(process.reinforcer.rationale ?? "")}</p>`
      : ""
  }</section>`;
}

function renderReportBrief(canvas) {
  if (!canvas.analysis_brief?.length) {
    return "";
  }
  return `<h2>System Overview</h2><div class="grid">${canvas.analysis_brief
    .map((brief) => `<section class="card"><p>${escapeHtml(brief)}</p></section>`)
    .join("")}</div>`;
}

function renderReportCanvas(canvas) {
  if (canvas.type === "quadrant") {
    return `<h2>Strategic Canvas</h2><div class="grid">${canvas.sections
      .map(
        (section) => `<section class="card"><h3>${escapeHtml(section.label)}</h3><p class="muted">${escapeHtml(section.prompt)}</p>${section.items
          .map((rawItem) => {
            const item = normalizeInsight(rawItem);
            return `<p><strong>${escapeHtml(item.text)}</strong></p>${item.rationale ? `<p class="muted">${escapeHtml(item.rationale)}</p>` : ""}${
              item.metric ? `<span class="tag">Metric: ${escapeHtml(item.metric)}</span>` : ""
            }`;
          })
          .join("")}</section>`
      )
      .join("")}</div>`;
  }

  if (canvas.type === "score_table") {
    const rows = canvas.rows ?? [];
    const maxScore = Math.max(...rows.map((row) => Number(row.score) || 0), 1);
    return `<h2>Prioritization Canvas</h2><table><thead><tr><th>Initiative</th><th>R</th><th>I</th><th>C</th><th>E</th><th>Score</th></tr></thead><tbody>${rows
      .map(
        (row) => `<tr><td><strong>${escapeHtml(row.initiative)}</strong><p class="muted">${escapeHtml(row.rationale ?? "")}</p></td><td>${row.reach}</td><td>${
          row.impact
        }</td><td>${row.confidence}%</td><td>${row.effort}</td><td><strong>${row.score}</strong><div class="bar"><div class="fill" style="width:${Math.max(
          8,
          ((Number(row.score) || 0) / maxScore) * 100
        )}%"></div></div></td></tr>`
      )
      .join("")}</tbody></table>`;
  }

  if (canvas.type === "framework_board") {
    return `<h2>${escapeHtml(canvas.title)}</h2><div class="grid">${canvas.lanes
      .map(
        (lane) => `<section class="card"><h3>${escapeHtml(lane.label)}</h3><p class="muted">${escapeHtml(lane.prompt)}</p>${lane.items
          .map((item) => `<p><strong>${escapeHtml(item.title)}</strong></p><p class="muted">${escapeHtml(item.body)}</p>${item.metric ? `<span class="tag">${escapeHtml(item.metric)}</span>` : ""}`)
          .join("")}</section>`
      )
      .join("")}</div>`;
  }

  if (canvas.type === "okr_board") {
    return `<h2>${escapeHtml(canvas.title)}</h2><div class="grid">${canvas.objectives
      .map(
        (objective) => `<section class="card"><h3>${escapeHtml(objective.objective)}</h3><p class="muted">${escapeHtml(objective.rationale)}</p>${objective.key_results
          .map((kr) => `<span class="tag">${escapeHtml(kr)}</span>`)
          .join("")}</section>`
      )
      .join("")}</div>`;
  }

  if (canvas.type === "force_map") {
    return `<h2>${escapeHtml(canvas.title)}</h2><div class="grid">${canvas.forces
      .map((force) => `<section class="card"><h3>${escapeHtml(force.name)} (${escapeHtml(force.intensity)})</h3><p>${escapeHtml(force.question)}</p><p class="muted">${escapeHtml(force.implication)}</p></section>`)
      .join("")}</div>`;
  }

  return `<h2>Contradiction Canvas</h2><section class="card"><p>${escapeHtml(canvas.contradiction?.prompt ?? "")}</p></section>`;
}

function renderReportFocus(focusCanvases) {
  if (!focusCanvases.length) {
    return `<h2>Focused Workspaces</h2><section class="card"><p class="muted">No focused workspaces were opened before export. Reopen the app, click Explore on an insight, and export again to include deeper notes.</p></section>`;
  }
  return `<h2>Focused Workspaces</h2>${focusCanvases
    .map(
      (focus) => `<section class="card"><div class="eyebrow">${escapeHtml(focus.eyebrow)}</div><h3>${escapeHtml(focus.title)}</h3><p class="muted">${escapeHtml(
        focus.description
      )}</p>${focus.panels
        .map(
          (panel) => `<h3>${escapeHtml(panel.title)}</h3><p>${escapeHtml(panel.value || panel.prompt)}</p>${(panel.options ?? [])
            .slice(0, 4)
            .map((option) => `<span class="tag">${escapeHtml(option)}</span>`)
            .join("")}`
        )
        .join("")}</section>`
    )
    .join("")}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
