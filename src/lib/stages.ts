export type StageId =
  | "functional"
  | "non_functional"
  | "entities_api"
  | "high_level"
  | "deep_dives";

export interface Stage {
  id: StageId;
  title: string;
  blurb: string;
  placeholder: string;
}

export const STAGES: Stage[] = [
  {
    id: "functional",
    title: "1. Functional Requirements",
    blurb:
      "What should the system do? List core user-visible capabilities. Mark anything out of scope.",
    placeholder:
      "Core:\n1. Users can ...\n2. ...\n\nOut of scope:\n- ...",
  },
  {
    id: "non_functional",
    title: "2. Non-Functional Requirements",
    blurb:
      "Latency, availability, consistency, durability, scale targets. Justify the tradeoffs you pick.",
    placeholder:
      "- Availability: 99.9%\n- Consistency: ... (and why)\n- Latency: p99 < ...\n- Scale: ... DAU, ... writes/s",
  },
  {
    id: "entities_api",
    title: "3. Core Entities & API",
    blurb:
      "List the primary objects and the API surface (HTTP methods, paths, request/response shape).",
    placeholder:
      "Entities:\n- User\n- File\n- ...\n\nAPI:\nPOST /files\nGET /files/{id}\n...",
  },
  {
    id: "high_level",
    title: "4. High-Level Design",
    blurb:
      "Walk through the architecture component by component, addressing each functional requirement.",
    placeholder:
      "Client → API Gateway → ...\n\nWrite path: ...\nRead path: ...\nStorage: ...",
  },
  {
    id: "deep_dives",
    title: "5. Deep Dives",
    blurb:
      "Pick 2-3 areas to go deep on (e.g. handling large files, hot keys, consistency, scaling). The interviewer will probe.",
    placeholder:
      "Deep dive 1: ...\nDeep dive 2: ...\nDeep dive 3: ...",
  },
];

export function stageById(id: StageId): Stage {
  const s = STAGES.find((x) => x.id === id);
  if (!s) throw new Error(`unknown stage: ${id}`);
  return s;
}

export type Level = "mid" | "senior" | "staff";

export const LEVELS: { id: Level; label: string; rubric: string }[] = [
  {
    id: "mid",
    label: "Mid (E4) — 80% breadth / 20% depth",
    rubric:
      "Expect a functional high-level design. Don't penalize missing depth on advanced topics like presigned URLs or chunking. Reward correct fundamentals.",
  },
  {
    id: "senior",
    label: "Senior (E5) — 60% breadth / 40% depth",
    rubric:
      "Expect quick high-level design and meaningful depth on at least one bottleneck. Push for tradeoffs and quantitative reasoning.",
  },
  {
    id: "staff",
    label: "Staff+ (E6+) — 40% breadth / 60% depth",
    rubric:
      "Expect proactivity and anticipation of failure modes. Critique quantitative back-of-envelope, consistency model choice, and operational concerns.",
  },
];
