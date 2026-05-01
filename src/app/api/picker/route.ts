import { NextRequest } from "next/server";
import { chat, extractJson } from "@/lib/llm";
import { buildDeepDivePickerPrompt } from "@/lib/prompts";
import { questionById } from "@/lib/questions";
import type { SessionState } from "@/lib/session";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

interface Body {
  session: SessionState;
}

interface PickerResponse {
  topics: string[];
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

  const messages = buildDeepDivePickerPrompt({ question, session: body.session });

  try {
    const raw = await chat(messages, { temperature: 0.3 });
    const parsed = extractJson<PickerResponse>(raw);
    const topics = (parsed.topics || [])
      .filter((t) => typeof t === "string" && t.trim().length > 0)
      .slice(0, 3);
    if (topics.length === 0) {
      return Response.json(
        { error: "model returned no topics" },
        { status: 500 },
      );
    }
    return Response.json({ topics });
  } catch (err) {
    return Response.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}
