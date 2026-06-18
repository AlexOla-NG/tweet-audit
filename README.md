# tweet-audit

Analyse your X (Twitter) archive using Gemini AI and flag tweets for deletion based on custom criteria.

## Overview

This tool processes your X archive, evaluates each tweet against your alignment criteria (e.g., unprofessional language, specific keywords, outdated opinions), and generates a list of tweet URLs marked for manual deletion.

## The Task

### Goal
Request an archive of your posts on X, analyse them using Google's Gemini AI, and flag tweets for deletion based on any criteria.

### Output
A CSV file containing flagged tweet URLs and a deletion status flag:
\`\`\`csv
tweet_url,deleted
https://x.com/username/status/1234567890,false
https://x.com/username/status/9876543210,false
\`\`\`

## Setup

### 1. Request Your X Archive
Download your archive from X Settings and extract the ZIP file.

### 2. Get Gemini API Key
Visit [Google AI Studio](https://aistudio.google.com/app/apikey) and add the key to \`config.json\`.

## Implementation

The tool follows a batch-processing architecture with AI-driven evaluation.

### Features
- **Batch Analysis:** Processes 50 tweets at a time.
- **Checkpointing:** Resume audits from where you left off.
- **Robust Parsing:** Handles X archive's JS/JSON format.
- **Detailed Logging:** Operational visibility via Python logging.

### Usage

1. **Configure**: Add \`gemini_api_key\`, \`username\`, and optionally \`model_name\` to \`config.json\`.
2. **Install**: \`pip install -r requirements.txt\`
3. **Run**: \`python main.py\`
4. **Review**: Check \`audit_results.csv\` for flagged tweets.

## Repository Structure
\`\`\`
tweet-audit/
├── main.py               # Audit Engine entry point
├── src/                  # Implementation (Parser, Evaluator)
├── tests/                # Unit tests
├── alignment_criteria.json # Your AI rules
├── config.json           # Local config (ignored)
└── TRADEOFFS.md          # Architectural decisions
\`\`\`

## Example Alignment Criteria
\`\`\`json
{
  "criteria": {
    "forbidden_words": ["crypto", "NFT"],
    "tone": "professional"
  }
}
\`\`\`
