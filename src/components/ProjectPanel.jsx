import { Loader2, MessageSquarePlus, ScrollText, Upload } from "lucide-react";
import { useRef, useState } from "react";
import ReactMarkdown from "react-markdown";

const DOCUMENT_MAX_CHARS = 500000;

export default function ProjectPanel({ goal, details, onChat, onImport }) {
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [importing, setImporting] = useState(false);
  const [summary, setSummary] = useState("");
  const [error, setError] = useState("");
  const fileInputRef = useRef(null);

  function describeError(err, fallback) {
    if (err?.status === 413 || err?.status === 422) {
      return "That text is too large or invalid for this field. Use Import document for large content.";
    }
    if (typeof err?.detail === "string" && err.detail) return err.detail;
    return fallback;
  }

  async function submit(event) {
    event?.preventDefault?.();
    const instruction = input.trim();
    if (!instruction || sending) return;
    setSending(true);
    setError("");
    try {
      const result = await onChat(instruction);
      setSummary(typeof result === "string" ? result : "");
      setInput("");
    } catch (err) {
      setError(describeError(err, "Could not update project details. Try again."));
    } finally {
      setSending(false);
    }
  }

  async function handleFile(event) {
    const file = event.target.files?.[0];
    event.target.value = ""; // allow re-selecting the same file
    if (!file || importing) return;
    setError("");
    let text = "";
    try {
      text = await file.text();
    } catch {
      setError("Could not read that file.");
      return;
    }
    if (!text.trim()) {
      setError("That file is empty.");
      return;
    }
    if (text.length > DOCUMENT_MAX_CHARS) {
      setError(`That document is too large (${text.length.toLocaleString()} chars; limit ${DOCUMENT_MAX_CHARS.toLocaleString()}).`);
      return;
    }
    setImporting(true);
    try {
      const result = await onImport(text, file.name);
      setSummary(typeof result === "string" ? result : "");
    } catch (err) {
      setError(describeError(err, "Could not import that document. Try again."));
    } finally {
      setImporting(false);
    }
  }

  return (
    <div className="max-w-3xl">
      <div className="animate-step inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/[0.06] px-3 py-2 text-sm text-white/72" style={{ animationDelay: "0.3s" }}>
        <ScrollText size={16} className="text-moss" />
        Active project workspace
      </div>

      <div className="animate-step mt-6" style={{ animationDelay: "0.45s" }}>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/40">Goal</p>
        <p className="mt-2 text-2xl font-semibold leading-8 text-white">{goal || "Untitled goal"}</p>
      </div>

      <div className="animate-step mt-6" style={{ animationDelay: "0.6s" }}>
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/40">Project Detail</p>
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={importing || sending}
            className="inline-flex items-center gap-1.5 rounded-md border border-white/15 bg-white/[0.05] px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.12em] text-white/72 transition hover:border-moss/50 hover:text-white disabled:opacity-50"
          >
            {importing ? <Loader2 size={12} className="animate-spin" /> : <Upload size={12} />}
            {importing ? "Importing..." : "Import document"}
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".md,.markdown,.txt,.text,text/markdown,text/plain"
            onChange={handleFile}
            className="hidden"
          />
        </div>
        <p className="mt-1 text-[11px] text-white/36">Read-only — change it with the chat below, or import a document to assimilate.</p>
        <div className="markdown-body mt-2 max-h-[42vh] overflow-y-auto rounded-lg border border-white/10 bg-[#07100d] p-4 text-sm leading-6 text-white/80">
          {details && details.trim() ? (
            <ReactMarkdown>{details}</ReactMarkdown>
          ) : (
            <p className="text-white/40">
              No project details yet. Use the box below to add information — for example, &ldquo;Add that our target users are mid-market logistics teams.&rdquo;
            </p>
          )}
        </div>
      </div>

      <form onSubmit={submit} className="animate-step mt-4" style={{ animationDelay: "0.75s" }}>
        <label className="text-xs font-semibold uppercase tracking-[0.18em] text-white/40" htmlFor="detail-chat">
          Add / update / remove information
        </label>
        <textarea
          id="detail-chat"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => {
            if ((event.metaKey || event.ctrlKey) && event.key === "Enter") submit(event);
          }}
          placeholder="e.g. Add that our budget is $50k, and remove the competitor section."
          className="mt-2 min-h-24 w-full resize-y rounded-lg border border-white/10 bg-[#07100d] px-4 py-3 text-sm leading-6 text-white caret-moss outline-none transition placeholder:text-white/32 focus:border-moss focus:ring-2 focus:ring-moss/20"
        />
        <div className="mt-3 flex items-center gap-3">
          <button
            type="submit"
            disabled={sending || !input.trim()}
            className="inline-flex items-center gap-2 rounded-lg bg-moss px-4 py-2.5 text-sm font-bold uppercase tracking-[0.12em] text-ink transition hover:bg-[#16A34A] disabled:cursor-wait disabled:opacity-60"
          >
            {sending ? <Loader2 size={16} className="animate-spin" /> : <MessageSquarePlus size={16} />}
            {sending ? "Updating..." : "Send"}
          </button>
          {summary && !error && <span className="text-xs text-white/52">{summary}</span>}
          {error && <span className="text-xs text-rose-300">{error}</span>}
        </div>
      </form>
    </div>
  );
}
