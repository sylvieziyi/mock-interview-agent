"use client";

import Link from "next/link";
import Markdown from "./Markdown";
import type { SessionSummary } from "@/lib/session";
import { stageById } from "@/lib/stages";

const VERDICT_LABEL: Record<SessionSummary["verdict"], string> = {
  strong_hire: "Strong Hire",
  hire: "Hire",
  lean_hire: "Lean Hire",
  lean_no: "Lean No-Hire",
  no_hire: "No Hire",
};

const VERDICT_COLOR: Record<SessionSummary["verdict"], string> = {
  strong_hire: "text-success border-success/40 bg-success/5",
  hire: "text-success border-success/30 bg-success/5",
  lean_hire: "text-warn border-warn/30 bg-warn/5",
  lean_no: "text-warn border-warn/40 bg-warn/5",
  no_hire: "text-danger border-danger/40 bg-danger/5",
};

export default function SummaryView({
  questionTitle,
  summary,
  savedTo,
}: {
  questionTitle: string;
  summary: SessionSummary;
  savedTo: string | null;
}) {
  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-bg/95 backdrop-blur">
      <div className="mx-auto max-w-3xl px-6 py-12">
        <div className="flex items-baseline justify-between gap-4">
          <div>
            <div className="text-xs uppercase tracking-widest text-text-mute">Interview verdict</div>
            <h1 className="mt-1 text-2xl font-semibold tracking-tight">{questionTitle}</h1>
          </div>
          <Link
            href="/"
            className="text-sm text-text-dim hover:text-text underline-offset-4 hover:underline"
          >
            ← back to all problems
          </Link>
        </div>

        <div className={`mt-6 rounded-xl border p-5 ${VERDICT_COLOR[summary.verdict]}`}>
          <div className="flex items-baseline justify-between">
            <div className="text-sm uppercase tracking-widest opacity-80">Verdict</div>
            <div className="text-xs opacity-70">overall {summary.overall} / 5</div>
          </div>
          <div className="mt-1 text-2xl font-semibold">{VERDICT_LABEL[summary.verdict]}</div>
        </div>

        <section className="mt-8">
          <h2 className="text-xs font-medium uppercase tracking-widest text-text-mute">
            Per-stage scores
          </h2>
          <ul className="mt-3 space-y-2">
            {summary.scores.map((s) => (
              <li
                key={s.stage}
                className="rounded-lg border border-border bg-surface/60 p-4 flex gap-4"
              >
                <div className="shrink-0 w-12 text-center">
                  <div className="text-xl font-semibold tabular-nums">{s.score}</div>
                  <div className="text-[10px] uppercase tracking-widest text-text-mute">/ 5</div>
                </div>
                <div className="min-w-0">
                  <div className="font-medium">{stageById(s.stage).title}</div>
                  <div className="mt-1 text-sm text-text-dim leading-relaxed">{s.reason}</div>
                </div>
              </li>
            ))}
          </ul>
        </section>

        <section className="mt-8 grid gap-4 md:grid-cols-2">
          <div className="rounded-lg border border-border bg-surface/60 p-4">
            <h3 className="text-xs font-medium uppercase tracking-widest text-success">
              Strengths
            </h3>
            <ul className="mt-3 space-y-1.5 text-sm text-text-dim list-disc pl-5">
              {summary.strengths.map((x, i) => <li key={i}>{x}</li>)}
            </ul>
          </div>
          <div className="rounded-lg border border-border bg-surface/60 p-4">
            <h3 className="text-xs font-medium uppercase tracking-widest text-danger">Gaps</h3>
            <ul className="mt-3 space-y-1.5 text-sm text-text-dim list-disc pl-5">
              {summary.gaps.map((x, i) => <li key={i}>{x}</li>)}
            </ul>
          </div>
        </section>

        <section className="mt-8 rounded-lg border border-border bg-surface/60 p-5">
          <h3 className="text-xs font-medium uppercase tracking-widest text-text-mute">
            Interviewer notes
          </h3>
          <div className="mt-3 text-sm text-text leading-relaxed">
            <Markdown>{summary.narrative}</Markdown>
          </div>
        </section>

        {savedTo && (
          <p className="mt-6 text-xs text-text-mute font-mono">
            saved → <span className="text-text-dim">{savedTo}/</span>
          </p>
        )}
      </div>
    </div>
  );
}
