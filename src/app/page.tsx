import Link from "next/link";
import { QUESTIONS } from "@/lib/questions";

export default function Home() {
  const sd = QUESTIONS.filter((q) => q.category === "system_design");
  const ml = QUESTIONS.filter((q) => q.category === "ml_system_design");

  return (
    <main className="min-h-screen">
      <header className="border-b border-border/60">
        <div className="mx-auto max-w-5xl px-6 py-10">
          <div className="flex items-baseline gap-3">
            <h1 className="text-2xl font-semibold tracking-tight">Mock Interview Agent</h1>
            <span className="text-xs uppercase tracking-widest text-text-mute">local · strict</span>
          </div>
          <p className="mt-3 max-w-2xl text-sm text-text-dim leading-relaxed">
            Senior system design mocks driven by an interviewer agent. It pushes back, picks
            deep dives based on your design, and scores you against the rubric at the end.
            Sessions save to disk locally.
          </p>
        </div>
      </header>

      <div className="mx-auto max-w-5xl px-6 py-10 grid gap-10">
        <Section title="System design" questions={sd} />
        <Section title="ML system design" questions={ml} />
      </div>
    </main>
  );
}

function Section({ title, questions }: { title: string; questions: typeof QUESTIONS }) {
  return (
    <section>
      <h2 className="text-xs font-medium uppercase tracking-widest text-text-mute">{title}</h2>
      <ul className="mt-4 grid gap-3 md:grid-cols-2">
        {questions.map((q) => (
          <li key={q.id}>
            <Link
              href={`/interview/${q.id}`}
              className="group block rounded-xl border border-border bg-surface/60 p-5 transition hover:border-border-strong hover:bg-surface"
            >
              <div className="flex items-baseline justify-between gap-3">
                <span className="font-medium tracking-tight">{q.title}</span>
                <span className="text-[10px] uppercase tracking-widest text-text-mute">
                  {q.difficulty}
                </span>
              </div>
              <p className="mt-2 text-sm text-text-dim line-clamp-3">{q.brief}</p>
              <div className="mt-3 flex items-center gap-2 text-xs text-accent opacity-0 transition group-hover:opacity-100">
                Start interview →
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
