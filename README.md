# Mock Interview Agent

A local, agent-driven mock interview tool for **system design** and **ML system design**.

Runs entirely on your machine via [Ollama](https://ollama.com) — no API keys, no per-call cost.

## What's in here

- **Excalidraw whiteboard** embedded in the interview view. Your diagram is serialized to text
  and fed to the interviewer agent so it can react to what you drew.
- **Free-form chat with a strict senior interviewer.** No turn-by-turn worksheet. The agent
  drives the conversation, demands quantification, and pushes back on hand-wavy claims.
- **Three agents working together:**
  - **Interviewer** — every chat turn. Strict L6/E6 bar-raiser persona. Asks one short question
    at a time, never gives the answer.
  - **Deep-Dive Picker** — runs once when you reach the deep-dives stage. Reads your design
    and picks 2–3 topics tailored to *your* gaps (not generic textbook topics).
  - **Evaluator** — runs at "End interview". Reads the full transcript + final diagram and
    produces rubric-aligned per-stage scores, a verdict (Strong Hire → No Hire), strengths,
    and gaps with quotes.
- **Sessions saved to disk** under `sessions/YYYY-MM-DD_HHMMSS_<question>/` (transcript JSON,
  diagram, summary JSON, summary markdown).
- **Free navigation** between stages — jump around as the conversation flows.

## Stages

1. Functional requirements
2. Non-functional requirements
3. Core entities & API
4. High-level design (whiteboard expected)
5. Deep dives (interviewer-driven Q&A)

Pick a target level (Mid / Senior / Staff+) and the rubric weights breadth vs depth accordingly.

## Setup

Prereqs: macOS, ~25 GB free disk, [Homebrew](https://brew.sh).

```bash
# Install Ollama and Node
brew install ollama node
brew services start ollama

# Pull the model (default: 14B, ~9 GB; fast and accurate enough)
ollama pull qwen3:14b

# Optional: for deeper feedback at the cost of latency (~20 GB)
ollama pull qwen3:32b

# Install JS deps and run
git clone https://github.com/sylvieziyi/mock-interview-agent.git
cd mock-interview-agent
cp .env.example .env
npm install
npm run dev
```

Open http://localhost:3000.

## Switching models

Edit `.env`:

```
OLLAMA_MODEL=qwen3:32b   # deeper, slower
# or
OLLAMA_MODEL=qwen3:14b   # default
```

Restart `npm run dev` after changing.

## Architecture

```
src/
  app/
    page.tsx                  Home: question picker
    interview/[id]/
      page.tsx                Server shell — looks up question, renders client
      InterviewClient.tsx     Orchestrator: state, agent calls, layout
    api/
      turn/route.ts           Interviewer agent (streaming)
      picker/route.ts         Deep-dive topic picker (JSON)
      finish/route.ts         Evaluator + write session to disk (JSON)
  components/
    ChatPanel.tsx             Transcript + input box
    StagePills.tsx            Stage navigator
    Whiteboard.tsx            Excalidraw wrapper (lazy, dark theme)
    SummaryView.tsx           Verdict + per-stage scores screen
    Markdown.tsx              react-markdown wrapper
  lib/
    llm.ts                    Ollama client (stream + JSON extract)
    prompts.ts                The three agent prompts
    diagram.ts                Excalidraw scene → text for the LLM
    session.ts                Session/Message/Summary types
    stages.ts                 Stage + level definitions
    questions.ts              Question bank
sessions/                     Saved interview transcripts (gitignored)
```

## Adding a question

Edit `src/lib/questions.ts`. Each entry is
`{ id, title, category, difficulty, brief, hints }`.

## Roadmap

- [x] Phase 1 — text-only, stateless feedback per stage
- [x] Phase 2 — agentic interviewer, Excalidraw whiteboard, deep-dive picker, scored verdict, session save
- [ ] Phase 3 — push-to-talk voice input via Web Speech API
- [ ] Cross-session progress tracking (which gaps recur?)
- [ ] More questions, especially ML system design

## Why local-only?

Per-call API cost adds up across many practice sessions. With Qwen3 14B on Apple Silicon you get
~25 tok/s and pretty solid feedback for $0.
