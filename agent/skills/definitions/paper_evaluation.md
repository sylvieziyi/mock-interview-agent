# paper_evaluation

## Description
Score and filter papers by relevance to user's interest areas. Uses the LLM to rate each paper on a 0-10 scale and assigns a primary category. Papers scoring below the threshold are discarded.

## Tools
- score_papers: Send a batch of papers (title + abstract) to the LLM. Returns a relevance score (0-10) and primary category for each paper.
- filter_by_threshold: Keep only papers with score >= configured minimum (default 7).

## Input
- papers: list of paper metadata dicts (from paper_discovery)
- topics: user's interest areas for scoring context
- min_score: minimum score threshold (default 7)

## Output
- scored_papers: list of papers with added fields: score (int 0-10), category (string)
