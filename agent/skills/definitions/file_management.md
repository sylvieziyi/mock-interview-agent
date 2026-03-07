# file_management

## Description
Download paper PDFs and organize them into a structured local file system. Papers are saved in date-based directories with category subfolders.

## Tools
- download_pdf: Download a paper's PDF from its URL. Saves to the organized folder structure.
- organize_files: Create the directory structure (YYYY/MM/DD/category/) and move/rename the PDF with a slugified title.

## Input
- summarized_papers: list of papers with metadata, scores, categories, and summaries
- base_path: root directory for paper storage (default: ~/Documents/MyAgent/papers/)

## Output
- papers_with_paths: same list with an added 'local_path' field (string, absolute path to saved PDF)
