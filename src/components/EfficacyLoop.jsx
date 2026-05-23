import { Check, Send } from "lucide-react";
import { useState } from "react";

import { sendFeedback } from "../lib/api";

const OUTCOMES = [
  { id: "clarified", label: "Clarified" },
  { id: "decided", label: "Decided" },
  { id: "acted", label: "Acted" },
  { id: "stalled", label: "Stalled" }
];

export default function EfficacyLoop({ goal, route }) {
  const [rating, setRating] = useState(4);
  const [outcome, setOutcome] = useState("clarified");
  const [comment, setComment] = useState("");
  const [status, setStatus] = useState("idle");

  if (!route) return null;

  async function submitFeedback() {
    setStatus("saving");
    await sendFeedback({
      goal,
      framework_id: route.framework_id,
      rating,
      outcome,
      comment,
      confidence: route.confidence
    });
    setStatus("saved");
  }

  return (
    <section id="feedback" className="border-t border-white/10 bg-[#101412] px-4 py-16 sm:px-6">
      <div className="mx-auto grid max-w-7xl gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-moss">Efficacy Loop</p>
          <h2 className="mt-3 text-3xl font-semibold text-white">Train the Wisdom Graph</h2>
          <p className="mt-4 max-w-xl text-sm leading-6 text-white/64">
            Rate whether the selected framework improved the decision. V1 stores this as append-only learning data
            for future routing improvements.
          </p>
        </div>

        <div className="glass-panel rounded-lg p-5">
          <div className="grid gap-5 sm:grid-cols-[0.8fr_1fr]">
            <div>
              <label className="text-sm font-medium text-white">Usefulness</label>
              <div className="mt-3 flex gap-2" data-testid="rating-buttons">
                {[1, 2, 3, 4, 5].map((value) => (
                  <button
                    key={value}
                    type="button"
                    onClick={() => setRating(value)}
                    className={`h-10 w-10 rounded-lg border text-sm font-semibold transition ${
                      rating === value
                        ? "border-moss bg-moss text-ink"
                        : "border-white/10 bg-white/[0.04] text-white hover:border-white/30"
                    }`}
                  >
                    {value}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-white">Outcome</label>
              <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
                {OUTCOMES.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setOutcome(item.id)}
                    className={`rounded-lg border px-3 py-2 text-xs font-semibold transition ${
                      outcome === item.id
                        ? "border-signal bg-signal text-ink"
                        : "border-white/10 bg-white/[0.04] text-white/72 hover:text-white"
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <textarea
            value={comment}
            onChange={(event) => setComment(event.target.value)}
            placeholder="Optional note: where did this framework help or miss?"
            className="mt-5 min-h-24 w-full resize-y rounded-lg border border-white/10 bg-[#07100d] px-4 py-3 text-sm text-white caret-moss outline-none transition placeholder:text-white/32 selection:bg-moss selection:text-ink focus:border-moss focus:ring-2 focus:ring-moss/20"
          />

          <button
            type="button"
            onClick={submitFeedback}
            disabled={status === "saving" || status === "saved"}
            className="mt-4 inline-flex items-center gap-2 rounded-lg bg-moss px-4 py-3 text-sm font-bold text-ink transition hover:bg-[#16A34A] disabled:cursor-not-allowed disabled:opacity-70"
            data-testid="submit-feedback"
          >
            {status === "saved" ? <Check size={17} /> : <Send size={17} />}
            {status === "saved" ? "Feedback stored" : status === "saving" ? "Storing..." : "Submit signal"}
          </button>
        </div>
      </div>
    </section>
  );
}
