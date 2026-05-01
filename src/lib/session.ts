import type { StageId } from "./stages";

export interface Message {
  id: string;
  role: "interviewer" | "candidate";
  text: string;
  stage: StageId;
  createdAt: string; // ISO
}

export interface SessionState {
  id: string;
  questionId: string;
  level: "mid" | "senior" | "staff";
  createdAt: string;
  currentStage: StageId;
  notes: Partial<Record<StageId, string>>;
  diagram: unknown | null; // Excalidraw scene JSON
  messages: Message[];
  deepDiveTopics: string[] | null;
  deepDiveIndex: number; // which deep dive topic we're on
}

export interface StageScore {
  stage: StageId;
  score: number; // 1-5
  reason: string;
}

export type Verdict = "strong_hire" | "hire" | "lean_hire" | "lean_no" | "no_hire";

export interface SessionSummary {
  scores: StageScore[];
  overall: number; // 1-5 average, rounded to 1 decimal
  verdict: Verdict;
  strengths: string[];
  gaps: string[];
  narrative: string; // 1-2 paragraph wrap-up
}

export function newSession(args: { questionId: string; level: SessionState["level"] }): SessionState {
  return {
    id: makeId(),
    questionId: args.questionId,
    level: args.level,
    createdAt: new Date().toISOString(),
    currentStage: "functional",
    notes: {},
    diagram: null,
    messages: [],
    deepDiveTopics: null,
    deepDiveIndex: 0,
  };
}

export function makeId(): string {
  return (
    Date.now().toString(36) +
    Math.random().toString(36).slice(2, 8)
  );
}
