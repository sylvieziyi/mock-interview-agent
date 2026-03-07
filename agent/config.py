"""Configuration for the AI Paper Agent."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# --- Topics & Filtering ---
TOPICS = [
    "LLM foundation models training scaling",
    "AI agents planning tool use reasoning",
    "agent context management skills memory",
    "multimodal vision language model",
    "AI infrastructure inference optimization",
    "LLM quantization distillation efficiency",
]

MIN_QUALITY_SCORE = 7  # Papers scoring below this are discarded (0-10 scale)

# --- Ollama / Qwen ---
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:7b"
SCORE_BATCH_SIZE = 5  # Number of papers to score per LLM call

# --- Paths ---
PROJECT_ROOT = Path(__file__).parent.parent
PAPERS_DIR = PROJECT_ROOT / "papers"
DATA_DIR = PROJECT_ROOT / "data"
SEEN_PAPERS_FILE = DATA_DIR / "seen_papers.json"
LOG_DIR = DATA_DIR / "logs"
SKILLS_DIR = Path(__file__).parent / "skills" / "definitions"

# --- Gmail ---
GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
GMAIL_RECIPIENT = os.getenv("GMAIL_RECIPIENT", GMAIL_USER)  # defaults to self
GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587

# --- Paper Sources ---
ARXIV_MAX_RESULTS = 50  # per topic query
SEMANTIC_SCHOLAR_MAX_RESULTS = 20  # per topic query
