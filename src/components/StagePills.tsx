"use client";

import { STAGES, type StageId } from "@/lib/stages";

const SHORT: Record<StageId, string> = {
  functional: "Functional",
  non_functional: "Non-functional",
  entities_api: "Entities & API",
  high_level: "High-level",
  deep_dives: "Deep dives",
};

export default function StagePills({
  current,
  onSelect,
}: {
  current: StageId;
  onSelect: (s: StageId) => void;
}) {
  return (
    <nav className="flex flex-wrap items-center gap-1.5">
      {STAGES.map((s, i) => {
        const active = s.id === current;
        return (
          <button
            key={s.id}
            onClick={() => onSelect(s.id)}
            className={[
              "text-xs px-3 py-1.5 rounded-full border transition",
              active
                ? "bg-accent/15 border-accent text-accent-strong"
                : "border-border text-text-dim hover:text-text hover:border-border-strong",
            ].join(" ")}
            title={s.blurb}
          >
            <span className="text-[10px] tabular-nums opacity-50 mr-1.5">{i + 1}</span>
            {SHORT[s.id]}
          </button>
        );
      })}
    </nav>
  );
}
