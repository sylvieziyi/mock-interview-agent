"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import ChatPanel from "@/components/ChatPanel";
import StagePills from "@/components/StagePills";
import SummaryView from "@/components/SummaryView";
import Whiteboard, { type WhiteboardHandle } from "@/components/Whiteboard";
import type { Question } from "@/lib/questions";
import {
  type SessionState,
  type SessionSummary,
  type Message,
  makeId,
  newSession,
} from "@/lib/session";
import { LEVELS, type Level, type StageId, stageById } from "@/lib/stages";

const STORAGE_KEY = (qid: string) => `mia:session:${qid}`;

export default function InterviewClient({ question }: { question: Question }) {
  const [session, setSession] = useState<SessionState | null>(null);
  const [chatInput, setChatInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [picking, setPicking] = useState(false);
  const [finishing, setFinishing] = useState(false);
  const [summary, setSummary] = useState<{ data: SessionSummary; savedTo: string | null } | null>(null);
  const [banner, setBanner] = useState<string | null>(null);
  const [briefOpen, setBriefOpen] = useState(true);
  const wbRef = useRef<WhiteboardHandle | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const openingTriggered = useRef(false);
  const diagramSaveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // load or create session on mount
  useEffect(() => {
    const stored = typeof window !== "undefined" && localStorage.getItem(STORAGE_KEY(question.id));
    if (stored) {
      try {
        setSession(JSON.parse(stored) as SessionState);
        return;
      } catch {
        /* fall through */
      }
    }
    setSession(newSession({ questionId: question.id, level: "senior" }));
  }, [question.id]);

  // persist on every session change
  useEffect(() => {
    if (!session) return;
    try {
      localStorage.setItem(STORAGE_KEY(question.id), JSON.stringify(session));
    } catch {
      /* quota / private mode — ignore */
    }
  }, [session, question.id]);

  // capture latest diagram before any LLM call
  const capturedSession = useCallback((s: SessionState): SessionState => {
    const scene = wbRef.current?.getScene();
    return scene ? { ...s, diagram: scene } : s;
  }, []);

  // debounced diagram persistence (Excalidraw fires onChange on every frame)
  const onDiagramChange = useCallback(
    (scene: { elements: unknown[]; appState: Record<string, unknown> }) => {
      if (diagramSaveTimer.current) clearTimeout(diagramSaveTimer.current);
      diagramSaveTimer.current = setTimeout(() => {
        setSession((s) => (s ? { ...s, diagram: scene } : s));
      }, 1500);
    },
    [],
  );

  // clean up the debounce timer on unmount
  useEffect(() => {
    return () => {
      if (diagramSaveTimer.current) clearTimeout(diagramSaveTimer.current);
    };
  }, []);

  // helper to call /api/turn streaming, mutating session.messages live
  const runInterviewerTurn = useCallback(
    async (sessionToSend: SessionState, isOpening = false) => {
      abortRef.current?.abort();
      const ac = new AbortController();
      abortRef.current = ac;
      setStreaming(true);

      // append a placeholder interviewer message that we'll fill in as chunks arrive
      const interviewerMsgId = makeId();
      setSession((s) =>
        s
          ? {
              ...s,
              messages: [
                ...s.messages,
                {
                  id: interviewerMsgId,
                  role: "interviewer",
                  text: "",
                  stage: s.currentStage,
                  createdAt: new Date().toISOString(),
                },
              ],
            }
          : s,
      );

      try {
        const res = await fetch("/api/turn", {
          method: "POST",
          signal: ac.signal,
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ session: sessionToSend, isOpening }),
        });
        if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const text = decoder.decode(value, { stream: true });
          if (!text) continue;
          setSession((s) =>
            s
              ? {
                  ...s,
                  messages: s.messages.map((m) =>
                    m.id === interviewerMsgId ? { ...m, text: m.text + text } : m,
                  ),
                }
              : s,
          );
        }
      } catch (err) {
        if ((err as Error).name === "AbortError") return;
        setSession((s) =>
          s
            ? {
                ...s,
                messages: s.messages.map((m) =>
                  m.id === interviewerMsgId
                    ? { ...m, text: m.text + `\n\n_[error: ${(err as Error).message}]_` }
                    : m,
                ),
              }
            : s,
        );
      } finally {
        setStreaming(false);
      }
    },
    [],
  );

  // kick off the opening once we have a session and there are no messages yet
  useEffect(() => {
    if (!session || openingTriggered.current) return;
    if (session.messages.length > 0) {
      openingTriggered.current = true;
      return;
    }
    openingTriggered.current = true;
    runInterviewerTurn(session, true);
  }, [session, runInterviewerTurn]);

  const onSend = useCallback(async () => {
    if (!session || !chatInput.trim() || streaming) return;
    const candidateMsg: Message = {
      id: makeId(),
      role: "candidate",
      text: chatInput.trim(),
      stage: session.currentStage,
      createdAt: new Date().toISOString(),
    };
    const next = capturedSession({ ...session, messages: [...session.messages, candidateMsg] });
    setSession(next);
    setChatInput("");
    await runInterviewerTurn(next);
  }, [session, chatInput, streaming, runInterviewerTurn, capturedSession]);

  const onSelectStage = useCallback(
    async (target: StageId) => {
      if (!session || streaming || picking) return;
      // update stage
      const updated = capturedSession({ ...session, currentStage: target });
      setSession(updated);

      // first time entering deep_dives → run picker, then auto-prompt interviewer
      if (target === "deep_dives" && !updated.deepDiveTopics) {
        setPicking(true);
        setBanner("Picking deep-dive topics tailored to your design…");
        try {
          const res = await fetch("/api/picker", {
            method: "POST",
            headers: { "content-type": "application/json" },
            body: JSON.stringify({ session: updated }),
          });
          const data = (await res.json()) as { topics?: string[]; error?: string };
          if (!res.ok || !data.topics) throw new Error(data.error || `HTTP ${res.status}`);
          const withTopics: SessionState = {
            ...updated,
            deepDiveTopics: data.topics,
            deepDiveIndex: 0,
          };
          setSession(withTopics);
          setBanner(`Deep-dive plan: ${data.topics.length} topic${data.topics.length === 1 ? "" : "s"}.`);
          await runInterviewerTurn(withTopics);
          setBanner(null);
        } catch (err) {
          setBanner(`Couldn't pick deep dives: ${(err as Error).message}`);
        } finally {
          setPicking(false);
        }
      }
    },
    [session, streaming, picking, runInterviewerTurn, capturedSession],
  );

  const onChangeLevel = useCallback(
    (lvl: Level) => {
      setSession((s) => (s ? { ...s, level: lvl } : s));
    },
    [],
  );

  const onChangeNotes = useCallback(
    (val: string) => {
      setSession((s) =>
        s ? { ...s, notes: { ...s.notes, [s.currentStage]: val } } : s,
      );
    },
    [],
  );

  const onFinish = useCallback(async () => {
    if (!session || streaming || finishing) return;
    setFinishing(true);
    const toSend = capturedSession(session);
    setSession(toSend);
    try {
      const res = await fetch("/api/finish", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ session: toSend }),
      });
      const data = (await res.json()) as {
        summary?: SessionSummary;
        savedTo?: string | null;
        error?: string;
      };
      if (!res.ok || !data.summary) throw new Error(data.error || `HTTP ${res.status}`);
      setSummary({ data: data.summary, savedTo: data.savedTo ?? null });
      // clear stored session — interview is done
      localStorage.removeItem(STORAGE_KEY(question.id));
    } catch (err) {
      alert(`Scoring failed: ${(err as Error).message}`);
    } finally {
      setFinishing(false);
    }
  }, [session, streaming, finishing, capturedSession, question.id]);

  const onResetSession = useCallback(() => {
    if (!confirm("Start over? This clears your current notes, diagram, and transcript.")) return;
    abortRef.current?.abort();
    openingTriggered.current = false;
    localStorage.removeItem(STORAGE_KEY(question.id));
    const fresh = newSession({ questionId: question.id, level: session?.level ?? "senior" });
    setSession(fresh);
    setChatInput("");
    setBanner(null);
  }, [question.id, session?.level]);

  const initialScene = useMemo(
    () =>
      session?.diagram && typeof session.diagram === "object"
        ? (session.diagram as { elements?: unknown[]; appState?: Record<string, unknown> })
        : null,
    [session?.id], // only on session swap (e.g. reset) — ignore live diagram updates
    // eslint-disable-next-line react-hooks/exhaustive-deps
  );

  if (!session) {
    return <div className="p-12 text-text-mute">Loading…</div>;
  }

  const stage = stageById(session.currentStage);
  const currentNotes = session.notes[session.currentStage] ?? "";

  return (
    <main className="h-screen flex flex-col">
      {/* header */}
      <header className="border-b border-border bg-surface/40 px-6 py-3 flex items-center gap-4">
        <Link
          href="/"
          className="text-xs text-text-mute hover:text-text whitespace-nowrap"
        >
          ← Problems
        </Link>
        <div className="min-w-0 flex-1">
          <div className="flex items-baseline gap-3">
            <h1 className="text-base font-semibold tracking-tight truncate">
              {question.title}
            </h1>
            <span className="text-[10px] uppercase tracking-widest text-text-mute">
              {question.difficulty}
            </span>
          </div>
        </div>
        <select
          value={session.level}
          onChange={(e) => onChangeLevel(e.target.value as Level)}
          disabled={streaming}
          className="text-xs bg-surface border border-border rounded-md px-2 py-1 text-text-dim disabled:opacity-50"
        >
          {LEVELS.map((l) => (
            <option key={l.id} value={l.id}>
              {l.label}
            </option>
          ))}
        </select>
        <button
          onClick={onResetSession}
          className="text-xs text-text-mute hover:text-danger transition"
          title="Discard this session and start fresh"
        >
          Reset
        </button>
      </header>

      {/* stage row */}
      <div className="border-b border-border px-6 py-2.5">
        <StagePills current={session.currentStage} onSelect={onSelectStage} />
        {session.currentStage === "deep_dives" && session.deepDiveTopics && (
          <ul className="mt-2 flex flex-wrap gap-1.5">
            {session.deepDiveTopics.map((t, i) => (
              <li
                key={i}
                className="text-[11px] text-text-mute border border-border rounded-full px-2.5 py-1"
                title={t}
              >
                <span className="opacity-50 mr-1">{i + 1}.</span>
                {t.length > 60 ? t.slice(0, 57) + "…" : t}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* main 2-column body */}
      <div className="flex-1 min-h-0 grid grid-cols-1 md:grid-cols-[minmax(0,1.4fr)_minmax(380px,0.9fr)] gap-4 p-4">
        {/* LEFT: brief + notes + whiteboard */}
        <div className="flex flex-col min-h-0 gap-3">
          <div className="rounded-xl border border-border bg-surface/60">
            <button
              onClick={() => setBriefOpen((v) => !v)}
              className="w-full flex items-center justify-between px-4 py-2.5 text-left"
            >
              <span className="text-xs font-medium uppercase tracking-widest text-text-mute">
                Problem brief
              </span>
              <span className="text-xs text-text-mute">{briefOpen ? "−" : "+"}</span>
            </button>
            {briefOpen && (
              <div className="px-4 pb-4 text-sm text-text-dim leading-relaxed">
                {question.brief}
              </div>
            )}
          </div>

          <div className="rounded-xl border border-border bg-surface/60 flex flex-col">
            <div className="px-4 py-2.5 border-b border-border flex items-baseline justify-between">
              <span className="text-xs font-medium uppercase tracking-widest text-text-mute">
                Your notes — {stage.title.replace(/^\d+\.\s*/, "")}
              </span>
              <span className="text-[10px] text-text-mute">{stage.blurb}</span>
            </div>
            <textarea
              value={currentNotes}
              onChange={(e) => onChangeNotes(e.target.value)}
              placeholder={stage.placeholder}
              className="resize-none bg-transparent px-4 py-3 text-sm font-mono text-text leading-relaxed focus:outline-none min-h-[140px]"
            />
          </div>

          <div className="flex-1 min-h-[280px] rounded-xl border border-border overflow-hidden">
            <Whiteboard
              initialScene={initialScene}
              apiRef={wbRef}
              onChange={onDiagramChange}
            />
          </div>
        </div>

        {/* RIGHT: chat */}
        <ChatPanel
          messages={session.messages}
          streaming={streaming || picking}
          input={chatInput}
          onInputChange={setChatInput}
          onSend={onSend}
          onFinish={onFinish}
          finishing={finishing}
          bannerText={banner}
        />
      </div>

      {summary && (
        <SummaryView
          questionTitle={question.title}
          summary={summary.data}
          savedTo={summary.savedTo}
        />
      )}
    </main>
  );
}
