# ai_paper_agent

## Description
Collect, evaluate, and curate AI research papers from arXiv.
Scores papers using multi-category weighted evaluation, downloads PDFs,
organizes them locally, and sends an HTML email digest.

## Capabilities
- Search arXiv with category filters (cs.AI, cs.CL, cs.LG, cs.CV)
- Score papers across multiple dimensions (relevance, novelty, impact, technical quality)
- Weighted topic priorities (agents > LLM/CL > infra/CV)
- Generate concise 3-sentence summaries
- Download PDFs and organize into dated category folders
- Send HTML email digest with per-category score breakdowns

## When to use
Use this skill when the user wants to:
- Find recent AI research papers
- Get a curated digest of papers on specific topics
- Download and organize academic papers
- Stay up to date with AI research

## Topics covered (by priority)
- AI Agents / Architecture / Planning / Memory (highest)
- LLM / Reasoning / Code Generation (medium)
- Inference Optimization / Quantization (lower)
- Vision-Language Models / Multimodal (lower)
