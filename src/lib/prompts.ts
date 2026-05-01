import type { ChatMessage } from "./llm";
import { diagramToText } from "./diagram";
import type { Question } from "./questions";
import type { SessionState } from "./session";
import { LEVELS, STAGES, stageById, type Level, type StageId } from "./stages";

const STAGE_FOCUS: Record<StageId, string> = {
  functional: `Stage focus: functional requirements. Push the candidate to list user-visible capabilities, NOT implementation details. Catch missing core flows. Force them to call out what's out-of-scope so we don't waste time.`,
  non_functional: `Stage focus: non-functional requirements. Demand quantitative targets (latency p99, availability %, scale numbers). Force them to take a side on consistency vs availability and justify it.`,
  entities_api: `Stage focus: entities and API. Push for concrete request/response shapes, correct HTTP methods, and proper REST design. Catch missing endpoints required by the functional reqs they listed.`,
  high_level: `Stage focus: high-level design. They should be drawing on the whiteboard. Walk both write path and read path. Probe storage choices and component responsibilities. Catch obvious bottlenecks.`,
  deep_dives: `Stage focus: deep dives. You have a list of deep-dive topics to drive through. Ask one at a time. Follow up if their answer is shallow. Move on once you've gotten enough signal.`,
};

const STRICT_PERSONA = `You are a senior staff engineer (Google L6 / Meta E6 bar-raiser) running a system design interview. You are STRICT. You do not coddle.

Your behavior:
- You do NOT give answers. You make the candidate reason.
- You push back on vague claims ("scalable", "fast", "robust") and demand specifics — numbers, mechanisms, alternatives considered.
- You quote the candidate's own words when calling out gaps.
- You catch implicit assumptions and force them surfaced.
- You probe tradeoffs, not happy paths. ("What breaks first as we scale? Why that and not the other thing?")
- You are conversational, not a lecturer. One short turn at a time. 2-4 sentences usually, max 6.
- You never write code or detailed system descriptions for them.
- If they say something flat-wrong, push with a counter-scenario rather than correcting.
- You move them along when they're stuck on the wrong thing. ("Park that. Let's get to the high-level design.")
- Use plain prose, not bullet lists. This is a conversation, not a graded worksheet.`;

function levelLine(level: Level): string {
  const l = LEVELS.find((x) => x.id === level)!;
  return `Target level: ${l.label}. Rubric: ${l.rubric}`;
}

function notesBlock(session: SessionState): string {
  const entries = STAGES.map((s) => {
    const n = (session.notes[s.id] || "").trim();
    return n ? `### ${s.title}\n${n}` : null;
  }).filter(Boolean);
  return entries.length ? entries.join("\n\n") : "(no notes yet)";
}

function diagramBlock(session: SessionState): string {
  return diagramToText(session.diagram);
}

function transcriptBlock(session: SessionState): string {
  if (session.messages.length === 0) return "(interview just started)";
  return session.messages
    .map((m) => `${m.role === "interviewer" ? "Interviewer" : "Candidate"}: ${m.text}`)
    .join("\n\n");
}

/**
 * Interviewer chat turn — generates the next interviewer message.
 * The candidate's latest message has already been appended to session.messages.
 */
export function buildInterviewerPrompt(args: {
  question: Question;
  session: SessionState;
  isOpening: boolean; // true for the very first message of the interview
}): ChatMessage[] {
  const { question, session, isOpening } = args;
  const stage = stageById(session.currentStage);
  const level = levelLine(session.level);

  const opening = isOpening
    ? `\n\nThis is the OPENING of the interview. Greet the candidate briefly (one sentence), state the problem in plain terms, and ask them to start with functional requirements. Do not lecture.`
    : "";

  const deepDiveContext =
    session.currentStage === "deep_dives" && session.deepDiveTopics
      ? `\n\nDeep-dive topics for this candidate (drive through them in roughly this order, but follow the conversation):\n${session.deepDiveTopics
          .map((t, i) => `${i + 1}. ${t}`)
          .join("\n")}\n\nFor each topic: ask, hear their answer, follow up 1-2x if shallow, then move to the next. Once you've worked through all topics, say something like "OK, let's wrap. Anything you'd revisit with more time?" to close the interview.`
      : "";

  const system = `${STRICT_PERSONA}

${level}

Current stage: ${stage.title}
${STAGE_FOCUS[session.currentStage]}${opening}${deepDiveContext}

Output: just the interviewer's next spoken turn. No "Interviewer:" prefix. No markdown headings. Plain conversational prose.`;

  const user = `# Problem
${question.title}

${question.brief}

# Candidate's structured notes (across all stages)
${notesBlock(session)}

# Candidate's whiteboard diagram
${diagramBlock(session)}

# Conversation so far
${transcriptBlock(session)}

Reply as the interviewer.`;

  return [
    { role: "system", content: system },
    { role: "user", content: user },
  ];
}

/**
 * Deep dive topic picker — runs ONCE when entering the deep_dives stage.
 * Returns 2-3 specific topics tailored to THIS candidate's design.
 */
export function buildDeepDivePickerPrompt(args: {
  question: Question;
  session: SessionState;
}): ChatMessage[] {
  const { question, session } = args;

  const system = `You are a senior staff engineer planning the deep-dive section of a system design interview at the ${session.level} level.

Look at the candidate's design and pick 2-3 deep-dive topics that will give the most signal. Each topic must:
- Be specific to THIS candidate's design (not a generic textbook topic)
- Target an area where their answer was vague, hand-wavy, or missing
- Be deep enough that they can't bluff through it in 30 seconds

Output STRICTLY this JSON (no markdown fences, no commentary):
{"topics": ["topic 1 phrased as a probing question", "topic 2", "topic 3"]}`;

  const user = `# Problem
${question.title}

${question.brief}

# Candidate's notes
${notesBlock(session)}

# Candidate's diagram
${diagramBlock(session)}

# Recent conversation
${transcriptBlock(session)}

Pick the deep-dive topics now.`;

  return [
    { role: "system", content: system },
    { role: "user", content: user },
  ];
}

/**
 * Evaluator — runs ONCE when the candidate ends the interview.
 * Returns rubric scores + verdict + summary as JSON.
 */
export function buildEvaluatorPrompt(args: {
  question: Question;
  session: SessionState;
}): ChatMessage[] {
  const { question, session } = args;
  const level = LEVELS.find((l) => l.id === session.level)!;

  const system = `You are a STRICT senior staff engineer scoring a system design interview at the ${level.label} level.

Rubric weighting: ${level.rubric}

Score each stage 1-5:
- 5 = excellent at this level
- 4 = strong, minor gaps
- 3 = meets bar
- 2 = below bar, notable gaps
- 1 = significant problems

Verdict scale (calibrated to ${session.level}):
- strong_hire: clearly above bar
- hire: at bar with confidence
- lean_hire: at bar with reservations
- lean_no: just below bar
- no_hire: clearly below bar

Be honest. Do not inflate. If they didn't address a stage, score it accordingly.

Output STRICTLY this JSON (no markdown fences, no commentary):
{
  "scores": [
    {"stage": "functional", "score": 4, "reason": "..."},
    {"stage": "non_functional", "score": 3, "reason": "..."},
    {"stage": "entities_api", "score": 3, "reason": "..."},
    {"stage": "high_level", "score": 4, "reason": "..."},
    {"stage": "deep_dives", "score": 3, "reason": "..."}
  ],
  "overall": 3.4,
  "verdict": "lean_hire",
  "strengths": ["specific strength 1 with quote", "..."],
  "gaps": ["specific gap 1 with quote", "..."],
  "narrative": "1-2 paragraph honest summary. Reference specific things they said or drew."
}`;

  const user = `# Problem
${question.title}

${question.brief}

# Candidate's notes
${notesBlock(session)}

# Candidate's final diagram
${diagramBlock(session)}

# Full transcript
${transcriptBlock(session)}

Score now.`;

  return [
    { role: "system", content: system },
    { role: "user", content: user },
  ];
}
