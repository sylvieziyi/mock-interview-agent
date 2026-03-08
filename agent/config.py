"""Configuration for the Junnie-Crew Agent."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# --- Topics & Filtering ---
# Each entry is (query, weight). Weight multiplies ARXIV_BASE_RESULTS:
#   weight 3 → 3x results fetched  (highest priority)
#   weight 2 → 2x results fetched  (medium priority)
#   weight 1 → 1x results fetched  (lower priority)
TOPICS: list[tuple[str, int]] = [
    # Agents (highest priority)
    ("cat:cs.AI LLM agent architecture planning tool use", 3),
    ("cat:cs.AI autonomous agent deep research task automation", 3),
    ("cat:cs.AI agent memory context management retrieval", 3),
    # LLM / CL (medium priority)
    ("cat:cs.CL large language model reasoning chain of thought", 2),
    ("cat:cs.CL LLM coding agent code generation", 2),
    # Infra / CV (lower priority)
    ("cat:cs.LG transformer inference optimization quantization distillation", 1),
    ("cat:cs.CV vision language model multimodal VLM", 1),
]

MIN_QUALITY_SCORE = 5.0  # Papers scoring below this (weighted avg) are discarded
MAX_FINAL_PAPERS = 20   # Max papers in final digest (top N by score)

# --- Scoring Categories ---
# Each category is scored 1-10 by the LLM, then combined via weighted average.
SCORING_CATEGORIES: dict[str, float] = {
    "relevance": 0.40,         # How relevant to user's interests
    "novelty": 0.25,           # How novel the approach or contribution
    "practical_impact": 0.20,  # Real-world applicability
    "technical_quality": 0.15, # Rigor and methodology
}

# --- Time Range ---
PAPER_TIME_RANGE_DAYS = 365  # Default: 1 year. Set to 730 for 2 years, 30 for 1 month, etc.

# --- Ollama / Qwen ---
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:7b"
SCORE_BATCH_SIZE = 5  # Number of papers to score per LLM call

# --- Paths ---
PROJECT_ROOT = Path(__file__).parent.parent
PAPERS_DIR = PROJECT_ROOT / "papers"
DATA_DIR = PROJECT_ROOT / "data"
LOG_DIR = DATA_DIR / "logs"

# --- Gmail ---
GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
GMAIL_RECIPIENT = os.getenv("GMAIL_RECIPIENT", GMAIL_USER)  # defaults to self
GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587

# --- Paper Sources ---
ARXIV_BASE_RESULTS = 30  # multiplied by topic weight to get per-topic fetch count
                         # agents: 3×30=90, CL/LG: 2×30=60, CV: 1×30=30

