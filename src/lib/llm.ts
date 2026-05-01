const BASE_URL = process.env.OLLAMA_BASE_URL ?? "http://127.0.0.1:11434";
const MODEL = process.env.OLLAMA_MODEL ?? "qwen3:14b";

export interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

interface ChatOpts {
  /** Lower = more deterministic. Default 0.4 for chat, lower for structured JSON. */
  temperature?: number;
  /** Reserve 8K context by default. */
  numCtx?: number;
}

export async function* streamChat(
  messages: ChatMessage[],
  opts: ChatOpts = {},
): AsyncGenerator<string> {
  const res = await fetch(`${BASE_URL}/api/chat`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      model: MODEL,
      messages,
      stream: true,
      options: {
        temperature: opts.temperature ?? 0.4,
        num_ctx: opts.numCtx ?? 8192,
      },
    }),
  });

  if (!res.ok || !res.body) {
    throw new Error(`Ollama error: ${res.status} ${await res.text().catch(() => "")}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    let nl = buf.indexOf("\n");
    while (nl !== -1) {
      const line = buf.slice(0, nl).trim();
      buf = buf.slice(nl + 1);
      if (line) {
        try {
          const json = JSON.parse(line);
          const chunk: string | undefined = json?.message?.content;
          if (chunk) yield chunk;
          if (json?.done) return;
        } catch {
          // tolerate partial lines
        }
      }
      nl = buf.indexOf("\n");
    }
  }
}

export async function chat(
  messages: ChatMessage[],
  opts: ChatOpts = {},
): Promise<string> {
  let out = "";
  for await (const chunk of streamChat(messages, opts)) out += chunk;
  return out;
}

/**
 * Strip the model's "thinking" output (Qwen3 emits <think>...</think> blocks
 * when reasoning). We don't want that in our final response.
 */
export function stripThinking(text: string): string {
  return text.replace(/<think>[\s\S]*?<\/think>\s*/gi, "").trim();
}

/**
 * Extract a JSON object from a model response. Handles cases where the model
 * wraps it in ```json fences or adds preamble text.
 */
export function extractJson<T>(raw: string): T {
  const cleaned = stripThinking(raw);

  // Try direct parse first
  try {
    return JSON.parse(cleaned) as T;
  } catch {
    // continue
  }

  // Try fenced
  const fenced = cleaned.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (fenced) {
    try {
      return JSON.parse(fenced[1]) as T;
    } catch {
      // continue
    }
  }

  // Try first { ... } block
  const start = cleaned.indexOf("{");
  const end = cleaned.lastIndexOf("}");
  if (start !== -1 && end > start) {
    const candidate = cleaned.slice(start, end + 1);
    return JSON.parse(candidate) as T;
  }

  throw new Error(`could not parse JSON from model response: ${cleaned.slice(0, 200)}…`);
}

export const llmConfig = { baseUrl: BASE_URL, model: MODEL };
