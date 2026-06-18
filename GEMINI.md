# Gemini Project Context: tweet-audit

## Project Overview
`tweet-audit` is a specialized tool designed to evaluate and flag X (formerly Twitter) posts for deletion. It leverages Google's Gemini AI to analyze tweet content against highly customizable "alignment criteria," such as professionalism, specific keywords, or shifts in personal opinion.

### Core Workflow
1. **Archive Input:** User provides their official X data archive.
2. **Analysis:** The tool parses the archive and evaluates each tweet using the Gemini API based on a JSON-defined criteria set.
3. **Output:** Generates a CSV file (`tweet_url,deleted`) listing tweets that should be removed.

## Architecture & Technology
- **AI Integration:** Uses \`google-genai\` SDK with \`gemini-2.5-flash\` as default.

- **Batching:** 50 tweets per batch for efficiency.
- **State Management:** Checkpointing via `.audit_checkpoint` file.
- **Logging:** Dual-stream logging (Console: simple, File: robust).
- **Config Management:** Sensitive information (API keys) is stored in `config.json` (ignored by git).

## Development Guidelines

### Implementation Priorities
- **Simplicity:** Manual deletion via CSV is the primary use case.
- **Reliability:** Handle API rate limits and potential network failures gracefully.
- **Privacy:** Ensure the archive data and API keys are never exposed or committed.

### Testing Standards
- **Mandatory Testing:** All implementation logic is covered by tests in the `tests/` directory.
- **Mocking:** Uses mocks for Gemini API interactions to avoid costs.

## Building and Running

### Prerequisites
- Python 3.10+

- **Install Dependencies:** `pip install -r requirements.txt`
- **Run Audit:** `python main.py`
- **Run Tests:** `python -m pytest`

## Key Files
- `main.py`: The Audit Engine entry point.
- `src/parser.py`: Logic for extracting tweets from JS archives.
- `src/evaluator.py`: AI-powered evaluation logic.
- `audit_results.csv`: The final report of flagged tweets.
- `TRADEOFFS.md`: Living document for implementation decisions.

## Additional Coding Preferences
- Keep project dependencies small
- Do not import libraries that you won't use.
