import { ArrowDown, ArrowUpRight, BrainCircuit, Check, Loader2, Network, Sparkles } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import CanvasWorkspace from "./components/CanvasWorkspace";
import EfficacyLoop from "./components/EfficacyLoop";
import FrameworkGalaxy from "./components/FrameworkGalaxy";
import FrameworkLibrary from "./components/FrameworkLibrary";
import { fetchFrameworks, routeGoal } from "./lib/api";

const STARTER_GOAL =
  "Prioritize our next AI product features while balancing user adoption, engineering effort, and demo impact.";

export default function App() {
  const [goal, setGoal] = useState(STARTER_GOAL);
  const [frameworks, setFrameworks] = useState([]);
  const [route, setRoute] = useState(null);
  const [pendingRoute, setPendingRoute] = useState(null);
  const [showFrameworkChooser, setShowFrameworkChooser] = useState(false);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");
  const workspaceRef = useRef(null);
  const goalInputRef = useRef(null);
  const routingRef = useRef(false);
  const routeActionRef = useRef(null);

  useEffect(() => {
    fetchFrameworks()
      .then(setFrameworks)
      .catch((err) => setError(err.message));
  }, []);

  const activeFrameworks = useMemo(() => frameworks.filter((framework) => framework.active), [frameworks]);

  async function handleRoute(event) {
    event?.preventDefault?.();
    if (routingRef.current) return;
    routingRef.current = true;
    const currentGoal = goalInputRef.current?.value?.trim() || goal.trim();
    setGoal(currentGoal);
    setStatus("routing");
    setError("");
    try {
      const result = await routeGoal(currentGoal);
      setPendingRoute(result);
      setShowFrameworkChooser(false);
      setStatus("reviewing");
      window.pendo?.track?.("omniframe_route_generated", {
        framework_id: result.framework_id,
        confidence: result.confidence
      });
    } catch (err) {
      setStatus("idle");
      setError(err.message);
    } finally {
      routingRef.current = false;
    }
  }

  function acceptRecommendedFramework() {
    if (!pendingRoute) return;
    setRoute(pendingRoute);
    setPendingRoute(null);
    setShowFrameworkChooser(false);
    setStatus("ready");
    setTimeout(() => workspaceRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 80);
  }

  async function chooseFramework(frameworkId) {
    const currentGoal = goalInputRef.current?.value?.trim() || goal.trim();
    setStatus("routing");
    setError("");
    try {
      const result = await routeGoal(currentGoal, frameworkId);
      setRoute(result);
      setPendingRoute(null);
      setShowFrameworkChooser(false);
      setStatus("ready");
      window.pendo?.track?.("omniframe_framework_override_selected", {
        framework_id: result.framework_id
      });
      setTimeout(() => workspaceRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 80);
    } catch (err) {
      setStatus("reviewing");
      setError(err.message);
    }
  }

  routeActionRef.current = handleRoute;

  useEffect(() => {
    const handleDocumentPointerDown = (event) => {
      const button = document.querySelector("[data-testid='route-button']");
      if (!button) return;
      const rect = button.getBoundingClientRect();
      const insideButton =
        event.clientX >= rect.left &&
        event.clientX <= rect.right &&
        event.clientY >= rect.top &&
        event.clientY <= rect.bottom;
      if (insideButton) {
        routeActionRef.current?.(event);
      }
    };

    document.addEventListener("pointerdown", handleDocumentPointerDown, true);
    return () => document.removeEventListener("pointerdown", handleDocumentPointerDown, true);
  }, []);

  return (
    <main className="min-h-screen overflow-hidden">
      <section className="relative min-h-screen border-b border-white/10 bg-ink">
        <FrameworkGalaxy frameworks={frameworks} activeId={route?.framework_id} />
        <div className="grid-fade pointer-events-none absolute inset-x-0 bottom-0 h-64" />
        <div className="relative z-10 mx-auto flex min-h-screen max-w-7xl flex-col px-4 py-5 sm:px-6">
          <header className="animate-step flex items-center justify-between" style={{ animationDelay: "0.1s" }}>
            <a href="#top" className="flex items-center gap-3 text-white">
              <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-moss text-ink shadow-glow">
                <BrainCircuit size={22} />
              </span>
              <span className="text-xl font-semibold tracking-tight">OmniFrame</span>
            </a>
            <nav className="hidden items-center gap-2 md:flex">
              {[
                ["Workspace", "#workspace"],
                ["Library", "#library"],
                ["Feedback", "#feedback"]
              ].map(([label, href]) => (
                <a key={label} href={href} className="rounded-lg px-3 py-2 text-sm text-white/64 transition hover:bg-white/10 hover:text-white">
                  {label}
                </a>
              ))}
            </nav>
          </header>

          <div className="grid flex-1 items-center gap-8 py-16 lg:grid-cols-[1.02fr_0.98fr]">
            <div className="max-w-3xl">
              <div className="animate-step inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/[0.06] px-3 py-2 text-sm text-white/72" style={{ animationDelay: "0.3s" }}>
                <Sparkles size={16} className="text-moss" />
                7 active routes now, 50-framework library ready
              </div>
              <h1 className="animate-step mt-6 max-w-4xl text-5xl font-semibold leading-[1.02] tracking-normal text-white sm:text-6xl lg:text-7xl" style={{ animationDelay: "0.55s" }}>
                CAD for thought, routed by an agentic strategy engine.
              </h1>
              <p className="animate-step mt-6 max-w-2xl text-base leading-7 text-white/68 sm:text-lg" style={{ animationDelay: "0.8s" }}>
                Enter a business or engineering goal. OmniFrame recommends the best framework first, then lets you accept it or choose any live route yourself.
              </p>

              <div className="animate-step mt-8 flex flex-wrap gap-3" style={{ animationDelay: "1s" }}>
                {activeFrameworks.map((framework) => (
                  <span key={framework.id} className="rounded-lg border border-white/10 bg-white/[0.06] px-3 py-2 text-sm text-white/76">
                    {framework.name}
                  </span>
                ))}
              </div>
            </div>

            <form onSubmit={handleRoute} className="animate-scale glass-panel rounded-lg p-5 shadow-glow" style={{ animationDelay: "0.7s" }}>
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.24em] text-moss">Agent Console</p>
                  <h2 className="mt-2 text-2xl font-semibold text-white">Route a goal</h2>
                </div>
                <Network className="text-signal" size={28} />
              </div>

              <label className="mt-5 block text-sm font-medium text-white/72" htmlFor="goal">
                Goal
              </label>
              <textarea
                id="goal"
                data-testid="goal-input"
                ref={goalInputRef}
                value={goal}
                onChange={(event) => setGoal(event.target.value)}
                onKeyDown={(event) => {
                  if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
                    handleRoute(event);
                  }
                }}
                className="mt-2 min-h-44 w-full resize-y rounded-lg border border-white/10 bg-[#07100d] px-4 py-3 text-base leading-7 text-white caret-moss outline-none transition placeholder:text-white/32 selection:bg-moss selection:text-ink focus:border-moss focus:ring-2 focus:ring-moss/20"
                placeholder="Example: Decide which AI feature to build first for our hackathon demo."
              />

              {error && <p className="mt-3 rounded-lg border border-red-400/30 bg-red-500/10 px-3 py-2 text-sm text-red-100">{error}</p>}

              <button
                type="button"
                onClick={handleRoute}
                onPointerDown={handleRoute}
                disabled={status === "routing"}
                className="group mt-5 flex w-full items-center justify-between rounded-lg bg-moss px-5 py-4 text-sm font-bold uppercase tracking-[0.16em] text-ink transition hover:bg-[#16A34A] disabled:cursor-wait disabled:opacity-70"
                data-testid="route-button"
              >
                <span>{status === "routing" ? "Routing..." : "Generate Canvas"}</span>
                <span className="flex h-9 w-9 items-center justify-center rounded-full bg-ink text-white transition group-hover:rotate-45">
                  {status === "routing" ? <Loader2 className="animate-spin" size={18} /> : <ArrowUpRight size={18} />}
                </span>
              </button>

              <a href="#library" className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-white/60 transition hover:text-white">
                Inspect future frameworks <ArrowDown size={16} />
              </a>
            </form>
          </div>
        </div>
      </section>

      <div ref={workspaceRef}>
        <CanvasWorkspace route={route} />
      </div>
      <FrameworkLibrary frameworks={frameworks} />
      <EfficacyLoop goal={goal} route={route} />

      <footer className="bg-[#0b0d0c] px-4 py-8 text-sm text-white/44 sm:px-6">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 border-t border-white/10 pt-6 md:flex-row md:items-center md:justify-between">
          <span>© 2026 Sciox, LLC. OmniFrame prototype.</span>
          <span>Novus by Pendo initialized anonymously at app entry.</span>
        </div>
      </footer>

      {pendingRoute && (
        <FrameworkDecisionModal
          pendingRoute={pendingRoute}
          activeFrameworks={activeFrameworks}
          showChooser={showFrameworkChooser}
          setShowChooser={setShowFrameworkChooser}
          onAccept={acceptRecommendedFramework}
          onChoose={chooseFramework}
          status={status}
        />
      )}
    </main>
  );
}

function FrameworkDecisionModal({ pendingRoute, activeFrameworks, showChooser, setShowChooser, onAccept, onChoose, status }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4 py-8 backdrop-blur-md">
      <section className="max-h-[92vh] w-full max-w-5xl overflow-y-auto rounded-lg border border-white/10 bg-[#0d1110] p-5 text-white shadow-[0_32px_100px_rgba(0,0,0,0.55)]">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-moss">Framework confirmation required</p>
            <h2 className="mt-3 text-3xl font-semibold">OmniFrame recommends {pendingRoute.framework_name}</h2>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-white/68">{pendingRoute.rationale}</p>
            <p className="mt-3 text-sm text-white/52">
              Review the logic before the canvas is generated. Accept the recommendation, or choose your own framework from the seven live routes.
            </p>
          </div>
          <div className="rounded-lg border border-moss/25 bg-moss/10 px-4 py-3 text-sm font-semibold text-moss">
            Confidence {Math.round(pendingRoute.confidence * 100)}%
          </div>
        </div>

        <div className="mt-6 grid gap-3 md:grid-cols-3">
          <div className="rounded-lg border border-white/10 bg-[#07100d] p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/36">Detected route</p>
            <p className="mt-2 text-lg font-semibold">{pendingRoute.framework_name}</p>
          </div>
          <div className="rounded-lg border border-white/10 bg-[#07100d] p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/36">Why this route</p>
            <p className="mt-2 text-sm leading-6 text-white/68">{pendingRoute.rationale}</p>
          </div>
          <div className="rounded-lg border border-white/10 bg-[#07100d] p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/36">Your control</p>
            <p className="mt-2 text-sm leading-6 text-white/68">Choose your own framework if you want a different analytical lens.</p>
          </div>
        </div>

        <div className="mt-6 flex flex-col gap-3 sm:flex-row">
          <button
            type="button"
            onClick={onAccept}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-moss px-5 py-3 text-sm font-bold uppercase tracking-[0.14em] text-ink transition hover:bg-signal"
          >
            <Check size={17} />
            Accept recommendation
          </button>
          <button
            type="button"
            onClick={() => setShowChooser(true)}
            className="rounded-lg border border-white/10 bg-white/[0.05] px-5 py-3 text-sm font-bold uppercase tracking-[0.14em] text-white transition hover:border-moss/50"
          >
            Choose your own
          </button>
        </div>

        {showChooser && (
          <div className="mt-6 rounded-lg border border-signal/30 bg-signal/10 p-4">
            <p className="text-sm font-semibold text-signal">Select one framework to proceed.</p>
            <p className="mt-1 text-sm text-white/62">The canvas will generate only after you click a framework card below.</p>
            <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {activeFrameworks.map((framework) => (
                <button
                  key={framework.id}
                  type="button"
                  onClick={() => onChoose(framework.id)}
                  disabled={status === "routing"}
                  className="depth-card rounded-lg border border-white/10 bg-[#07100d] p-4 text-left transition hover:border-moss/60 disabled:cursor-wait disabled:opacity-60"
                >
                  <p className="text-xs font-semibold text-moss">Rank {framework.rank}</p>
                  <h3 className="mt-2 text-lg font-semibold text-white">{framework.name}</h3>
                  <p className="mt-2 text-sm leading-6 text-white/56">{framework.selection_lens}</p>
                </button>
              ))}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
