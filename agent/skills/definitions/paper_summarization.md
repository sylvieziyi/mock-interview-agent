# paper_summarization

## Description
Generate concise summaries of selected papers using the LLM. Each summary captures the key contribution, method, and findings in 3 sentences.

## Tools
- summarize_paper: Send paper title and abstract to the LLM. Returns a 3-sentence summary highlighting: what problem it solves, the approach, and key results.

## Input
- scored_papers: list of papers that passed the quality filter (from paper_evaluation)

## Output
- summarized_papers: same list with an added 'summary' field (string, 3 sentences)
