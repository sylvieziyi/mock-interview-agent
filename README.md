# junnie-crew

A personal AI agent framework that runs entirely on your local machine. Named after Junnie the cat.

The first skill is an **AI Paper Agent** that collects, scores, and curates research papers from arXiv, then sends you an email digest.

## Architecture

```
agent/
  main.py              # CLI entry point (--dry-run, --goal, --skill)
  planner.py           # Generic skill selector (LLM picks which skill to run)
  context.py           # 3-layer memory (working, short-term session, long-term persistent)
  config.py            # All configuration in one place

  shared/              # Reusable utilities (not domain-specific)
    llm.py             #   Ollama/Qwen interface
    email.py           #   Gmail SMTP
    file_ops.py        #   File download, slugify, ensure_dir

  tools/               # Domain tools (shared across skills)
    fetchers.py        #   arXiv API with category filters + weighted topics
    scorer.py          #   Multi-category LLM scoring (relevance, novelty, impact, quality)
    summarizer.py      #   Paper summarization via LLM

  skills/              # Pluggable skills (1 skill = 1 use case)
    registry.py        #   Auto-discovers skills from subdirectories
    ai_paper_agent/    #   Paper collection skill
      skill.md         #     LLM-readable description (loaded by planner)
      executor.py      #     Pipeline: fetch → dedup → score → summarize → download → notify
```

**Key design decisions:**
- **Coarse-grained skills** — each skill is a complete use case, not a micro-step
- **Skills are Markdown** — `skill.md` files are read directly as LLM context
- **Tools are shared** — `agent/tools/` is separate from skills so tools can be reused
- **Generic planner** — selects which skill to run based on user goal, not step-by-step planning

## Setup

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai) with Qwen 2.5 7B model

```bash
# Install Ollama, then pull the model
ollama pull qwen2.5:7b
```

### Install

```bash
git clone https://github.com/sylvieziyi/junnie-crew.git
cd junnie-crew
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configure email (optional)

```bash
cp .env.example .env
# Edit .env with your Gmail address and App Password
# To get an App Password: Google Account → Security → 2-Step Verification → App Passwords
```

## Usage

```bash
# Dry run (no LLM calls, no downloads, no email)
python3 -m agent.main --skill ai_paper_agent --dry-run

# Full run
python3 -m agent.main --skill ai_paper_agent

# Let the planner pick the skill based on a goal
python3 -m agent.main --goal "find me the latest AI agent papers"
```

## AI Paper Agent

### How it works

1. **Fetch** — Queries arXiv with category-filtered searches (`cat:cs.AI`, `cs.CL`, `cs.LG`, `cs.CV`)
2. **Dedup** — Removes papers seen in previous runs (long-term memory)
3. **Score** — Multi-category LLM scoring across 4 dimensions:
   | Category | Weight | What it measures |
   |---|---|---|
   | Relevance | 40% | How relevant to your interests |
   | Novelty | 25% | How novel the approach |
   | Practical Impact | 20% | Real-world applicability |
   | Technical Quality | 15% | Rigor and methodology |
4. **Filter** — Keeps papers above score threshold, takes top 20
5. **Summarize** — 3-sentence summary via LLM
6. **Download** — PDFs organized into `papers/YYYY/MM/DD/category/`
7. **Notify** — HTML email digest with per-category score breakdowns

### Topic priorities

Topics are weighted so agent papers get more fetch quota:

| Priority | Categories | Fetch multiplier |
|---|---|---|
| Highest | AI agents, planning, memory, deep research | 3x |
| Medium | LLM reasoning, code generation | 2x |
| Lower | Inference optimization, multimodal/VLM | 1x |

Edit topics in `agent/config.py`.

## Memory

Three layers of context management:

- **Working memory** — in-process key-value store for current run
- **Short-term (session)** — JSON logs saved per run (`data/sessions/`)
- **Long-term** — persistent state across runs (`data/long_term_memory.json`), tracks seen paper IDs to avoid duplicates

Checkpoints are saved at each pipeline stage for crash recovery (`data/checkpoints/`).

## Adding a new skill

1. Create `agent/skills/your_skill/skill.md` — describe what the skill does
2. Create `agent/skills/your_skill/executor.py` — implement `execute(context, dry_run)`
3. The registry auto-discovers it. Run with `--skill your_skill`

## Cost

$0/month. Everything runs locally:
- Qwen 2.5 7B via Ollama (free, local)
- arXiv API (free, no key needed)
- Gmail SMTP (free with App Password)

## License

MIT
