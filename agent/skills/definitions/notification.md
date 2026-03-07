# notification

## Description
Send a daily email digest of curated papers to the user's Gmail. The email includes paper titles, AI-generated summaries, links to the original paper, and local file paths.

## Tools
- send_email_digest: Compose and send an HTML email via Gmail SMTP with all curated papers for the day.

## Input
- papers_with_paths: list of fully processed papers (title, summary, url, category, score, local_path)
- recipient: email address to send the digest to

## Output
- email_sent: boolean indicating success
- papers_count: number of papers included in the digest
