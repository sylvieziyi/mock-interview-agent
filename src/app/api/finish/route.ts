import { NextRequest } from "next/server";
import { promises as fs } from "node:fs";
import path from "node:path";
import { chat, extractJson } from "@/lib/llm";
import { buildEvaluatorPrompt } from "@/lib/prompts";
import { questionById } from "@/lib/questions";
import type { SessionState, SessionSummary } from "@/lib/session";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

interface Body {
  session: SessionState;
}

export async function POST(req: NextRequest) {
  let body: Body;
  try {
    body = (await req.json()) as Body;
  } catch {
    return Response.json({ error: "invalid json" }, { status: 400 });
  }

  const question = questionById(body.session.questionId);
  if (!question) return Response.json({ error: "unknown question" }, { status: 404 });

  const messages = buildEvaluatorPrompt({ question, session: body.session });

  let summary: SessionSummary;
  try {
    const raw = await chat(messages, { temperature: 0.2 });
    summary = extractJson<SessionSummary>(raw);
  } catch (err) {
    return Response.json(
      { error: `evaluator failed: ${err instanceof Error ? err.message : String(err)}` },
      { status: 500 },
    );
  }

  // Save session to disk: sessions/YYYY-MM-DD_HHMMSS_questionId/
  const date = new Date(body.session.createdAt);
  const ymd = date.toISOString().slice(0, 10);
  const hms = date.toTimeString().slice(0, 8).replace(/:/g, "");
  const dirName = `${ymd}_${hms}_${body.session.questionId}`;
  const sessionsRoot = path.join(process.cwd(), "sessions");
  const dir = path.join(sessionsRoot, dirName);
  let savedTo: string | null = null;

  try {
    await fs.mkdir(dir, { recursive: true });
    await fs.writeFile(
      path.join(dir, "transcript.json"),
      JSON.stringify(body.session, null, 2),
      "utf8",
    );
    if (body.session.diagram) {
      await fs.writeFile(
        path.join(dir, "diagram.excalidraw"),
        JSON.stringify(body.session.diagram, null, 2),
        "utf8",
      );
    }
    await fs.writeFile(
      path.join(dir, "summary.json"),
      JSON.stringify(summary, null, 2),
      "utf8",
    );
    await fs.writeFile(path.join(dir, "summary.md"), renderMarkdown(question.title, body.session, summary), "utf8");
    savedTo = path.relative(process.cwd(), dir);
  } catch (err) {
    // session save failure shouldn't block returning the summary
    console.error("session save failed:", err);
  }

  return Response.json({ summary, savedTo });
}

function renderMarkdown(title: string, session: SessionState, s: SessionSummary): string {
  const verdictLabel: Record<string, string> = {
    strong_hire: "Strong Hire",
    hire: "Hire",
    lean_hire: "Lean Hire",
    lean_no: "Lean No-Hire",
    no_hire: "No Hire",
  };
  const stageTitle: Record<string, string> = {
    functional: "Functional requirements",
    non_functional: "Non-functional requirements",
    entities_api: "Entities & API",
    high_level: "High-level design",
    deep_dives: "Deep dives",
  };
  const lines: string[] = [];
  lines.push(`# ${title} — ${verdictLabel[s.verdict] || s.verdict}`);
  lines.push("");
  lines.push(`**Level:** ${session.level}`);
  lines.push(`**Overall:** ${s.overall} / 5`);
  lines.push(`**Date:** ${session.createdAt}`);
  lines.push("");
  lines.push(`## Per-stage scores`);
  for (const sc of s.scores) {
    lines.push(`- **${stageTitle[sc.stage] || sc.stage}** — ${sc.score}/5 — ${sc.reason}`);
  }
  lines.push("");
  lines.push(`## Strengths`);
  for (const x of s.strengths) lines.push(`- ${x}`);
  lines.push("");
  lines.push(`## Gaps`);
  for (const x of s.gaps) lines.push(`- ${x}`);
  lines.push("");
  lines.push(`## Narrative`);
  lines.push(s.narrative);
  return lines.join("\n");
}
