import { NextRequest } from "next/server";
import { streamChat } from "@/lib/llm";
import { buildInterviewerPrompt } from "@/lib/prompts";
import { questionById } from "@/lib/questions";
import type { SessionState } from "@/lib/session";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

interface Body {
  session: SessionState;
  isOpening?: boolean;
}

export async function POST(req: NextRequest) {
  let body: Body;
  try {
    body = (await req.json()) as Body;
  } catch {
    return new Response("invalid json", { status: 400 });
  }

  const question = questionById(body.session.questionId);
  if (!question) return new Response("unknown question", { status: 404 });

  const messages = buildInterviewerPrompt({
    question,
    session: body.session,
    isOpening: body.isOpening ?? false,
  });

  const encoder = new TextEncoder();
  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      try {
        // Strip <think>...</think> blocks on the fly so the user never sees them
        let buffer = "";
        let inThink = false;
        for await (const chunk of streamChat(messages, { temperature: 0.5 })) {
          buffer += chunk;
          // process tokens that may include <think> markers
          // strip <think>...</think>; preserve up to 8 trailing chars in case
          // a tag straddles a chunk boundary (e.g. "</thi" + "nk>")
          const TAIL = 8;
          while (true) {
            if (inThink) {
              const close = buffer.indexOf("</think>");
              if (close === -1) {
                if (buffer.length > TAIL) buffer = buffer.slice(buffer.length - TAIL);
                break;
              }
              buffer = buffer.slice(close + "</think>".length);
              inThink = false;
            } else {
              const open = buffer.indexOf("<think>");
              if (open === -1) {
                if (buffer.length > TAIL) {
                  const flush = buffer.slice(0, buffer.length - TAIL);
                  if (flush) controller.enqueue(encoder.encode(flush));
                  buffer = buffer.slice(buffer.length - TAIL);
                }
                break;
              }
              const flush = buffer.slice(0, open);
              if (flush) controller.enqueue(encoder.encode(flush));
              buffer = buffer.slice(open + "<think>".length);
              inThink = true;
            }
          }
        }
        if (!inThink && buffer) controller.enqueue(encoder.encode(buffer));
        controller.close();
      } catch (err) {
        controller.enqueue(
          encoder.encode(
            `\n\n[error talking to Ollama: ${err instanceof Error ? err.message : String(err)}]\n` +
              `Make sure Ollama is running and the model is pulled.`,
          ),
        );
        controller.close();
      }
    },
  });

  return new Response(stream, {
    headers: {
      "content-type": "text/plain; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}
