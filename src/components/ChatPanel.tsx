"use client";

import { useEffect, useRef } from "react";
import Markdown from "./Markdown";
import type { Message } from "@/lib/session";
import type { StageId } from "@/lib/stages";

const STAGE_BADGE: Record<StageId, string> = {
  functional: "FR",
  non_functional: "NFR",
  entities_api: "API",
  high_level: "HL",
  deep_dives: "DD",
};

export default function ChatPanel({
  messages,
  streaming,
  input,
  onInputChange,
  onSend,
  onFinish,
  finishing,
  bannerText,
}: {
  messages: Message[];
  streaming: boolean;
  input: string;
  onInputChange: (v: string) => void;
  onSend: () => void;
  onFinish: () => void;
  finishing: boolean;
  bannerText?: string | null;
}) {
  const scrollerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollerRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [messages, streaming]);

  return (
    <div className="flex flex-col h-full min-h-0 rounded-xl border border-border bg-surface/60">
      <div className="px-4 py-2.5 border-b border-border flex items-center justify-between">
        <div className="text-xs font-medium uppercase tracking-widest text-text-mute">
          Interviewer
        </div>
        <button
          onClick={onFinish}
          disabled={finishing || streaming || messages.length < 2}
          className="text-xs px-2.5 py-1 rounded-md border border-border text-text-dim hover:text-danger hover:border-danger/60 disabled:opacity-40 disabled:cursor-not-allowed transition"
          title="End the interview and get scored"
        >
          {finishing ? "Scoring…" : "End interview"}
        </button>
      </div>

      <div ref={scrollerRef} className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {bannerText && (
          <div className="rounded-md border border-accent/30 bg-accent/5 px-3 py-2 text-xs text-accent-strong fade-in">
            {bannerText}
          </div>
        )}
        {messages.length === 0 && !streaming && !bannerText && (
          <div className="text-sm text-text-mute italic">Waiting for the interviewer…</div>
        )}
        {messages.map((m) => (
          <Bubble key={m.id} message={m} />
        ))}
        {streaming && messages.at(-1)?.role !== "interviewer" && (
          <div className="text-xs text-text-mute italic animate-pulse">interviewer is typing…</div>
        )}
      </div>

      <div className="border-t border-border p-3 flex gap-2 items-end">
        <textarea
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey) && input.trim() && !streaming) {
              e.preventDefault();
              onSend();
            }
          }}
          rows={3}
          placeholder="Reply to the interviewer…  (⌘/Ctrl + Enter to send)"
          className="flex-1 resize-none rounded-md border border-border bg-bg/40 px-3 py-2 text-sm text-text placeholder:text-text-mute focus:outline-none focus:border-accent/60"
        />
        <button
          disabled={streaming || !input.trim()}
          onClick={onSend}
          className="rounded-md bg-accent text-bg px-4 py-2 text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:bg-accent-strong transition"
        >
          Send
        </button>
      </div>
    </div>
  );
}

function Bubble({ message }: { message: Message }) {
  const isInterviewer = message.role === "interviewer";
  return (
    <div className="fade-in">
      <div className="flex items-baseline gap-2 mb-1">
        <span
          className={[
            "text-[10px] uppercase tracking-widest font-medium",
            isInterviewer ? "text-accent-strong" : "text-success",
          ].join(" ")}
        >
          {isInterviewer ? "Interviewer" : "You"}
        </span>
        <span className="text-[10px] text-text-mute font-mono">
          {STAGE_BADGE[message.stage]}
        </span>
      </div>
      <div
        className={[
          "rounded-lg px-3 py-2 text-sm leading-relaxed",
          isInterviewer
            ? "bg-accent/8 border border-accent/20 text-text"
            : "bg-surface-2 border border-border text-text-dim",
        ].join(" ")}
      >
        {isInterviewer ? <Markdown>{message.text}</Markdown> : <span className="whitespace-pre-wrap">{message.text}</span>}
      </div>
    </div>
  );
}
