# paper_discovery

## Description
Search and collect AI-related papers from multiple academic sources. Gathers raw paper metadata including titles, abstracts, URLs, and source identifiers.

## Tools
- search_arxiv: Search arXiv for papers matching topic keywords. Returns title, abstract, arxiv_id, pdf_url.
- search_huggingface: Fetch today's trending papers from HuggingFace daily papers page. Returns title, abstract, url.
- search_papers_with_code: Query Papers With Code API for recent trending papers. Returns title, abstract, url, arxiv_id.
- search_semantic_scholar: Search Semantic Scholar by topic keywords. Returns title, abstract, doi, url.

## Input
- topics: list of topic keyword strings from user config

## Output
- papers: list of paper metadata dicts, each with keys: title, abstract, url, source, arxiv_id (if available), doi (if available)
