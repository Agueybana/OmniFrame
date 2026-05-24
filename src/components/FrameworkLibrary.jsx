import { Lock, Sparkles } from "lucide-react";
import { useMemo, useState } from "react";

export default function FrameworkLibrary({ frameworks = [] }) {
  const [filter, setFilter] = useState("all");
  const activeCount = frameworks.filter((framework) => framework.active).length;
  const visible = useMemo(() => {
    if (filter === "active") return frameworks.filter((framework) => framework.active);
    if (filter === "future") return frameworks.filter((framework) => !framework.active);
    return frameworks;
  }, [filter, frameworks]);

  return (
    <section id="library" className="bg-[#f6f8f5] px-4 py-16 text-ink sm:px-6">
      <div className="mx-auto max-w-7xl">
        <div className="flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-[#17783a]">Framework Library</p>
            <h2 className="mt-3 text-3xl font-semibold">50 methodologies, {activeCount} live routes</h2>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-black/60">
              The full reference catalog is stored in the backend. V1 now activates the seven strongest prototype routes while the rest
              stay visible as deliberately scoped future additions.
            </p>
          </div>

          <div className="flex rounded-lg border border-black/10 bg-white p-1">
            {["all", "active", "future"].map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => setFilter(item)}
                className={`rounded-md px-4 py-2 text-sm font-semibold capitalize transition ${
                  filter === item ? "bg-ink text-white" : "text-black/60 hover:text-black"
                }`}
              >
                {item}
              </button>
            ))}
          </div>
        </div>

        <div className="mt-8 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {visible.map((framework) => (
            <article key={framework.id} className="rounded-lg border border-black/10 bg-white p-4 shadow-sm">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold text-black/40">Rank {framework.rank}</p>
                  <h3 className="mt-1 text-lg font-semibold">{framework.name}</h3>
                </div>
                <span
                  className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-bold ${
                    framework.active ? "bg-[#dffbe8] text-[#147136]" : "bg-black/[0.06] text-black/48"
                  }`}
                >
                  {framework.active ? <Sparkles size={13} /> : <Lock size={13} />}
                  {framework.active ? "Live" : "Future"}
                </span>
              </div>
              <p className="mt-3 text-sm font-medium text-black/72">{framework.core_components}</p>
              <p className="mt-3 text-sm leading-6 text-black/56">{framework.selection_lens}</p>
              <div className="mt-4 border-t border-black/10 pt-3 text-xs leading-5 text-black/48">
                <p>{framework.alternatives}</p>
                <p>{framework.usage_rights}</p>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
