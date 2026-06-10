# Gemini Project Context: tweet-audit

## Project Overview
`tweet-audit` is a specialized tool designed to evaluate and flag X (formerly Twitter) posts for deletion. It leverages Google's Gemini AI to analyze tweet content against highly customizable "alignment criteria," such as professionalism, specific keywords, or shifts in personal opinion.

### Core Workflow
1. **Archive Input:** User provides their official X data archive.
2. **Analysis:** The tool parses the archive and evaluates each tweet using the Gemini API based on a JSON-defined criteria set.
3. **Output:** Generates a CSV file (`tweet_url,deleted`) listing tweets that should be removed.

## Architecture & Technology
The project is currently in its initial setup phase. The following requirements are established:
- **AI Integration:** Must use Google's Gemini API for tweet evaluation.
- **Config Management:** Sensitive information (API keys) is stored in `config.json` (ignored by git).
- **Documentation:** Architectural decisions, concurrency strategies, and error handling must be documented in `TRADEOFFS.md`.

## Development Guidelines

### Implementation Priorities
- **Simplicity:** Manual deletion via CSV is the primary use case; automated deletion via X API is considered optional/overkill.
- **Reliability:** Handle API rate limits and potential network failures gracefully.
- **Privacy:** Ensure the archive data and API keys are never exposed or committed.

### Testing Standards
- **Mandatory Testing:** All implementation logic must be covered by tests in the `tests/` directory.
- **Mocking:** Use mocks for Gemini API interactions to avoid unnecessary costs and dependency on live network calls during tests.

## Building and Running

### Prerequisites
- Python

- **Install Dependencies:** `pip install`
- **Run Audit:** `python main.py`
- **Run Tests:** `pytest`

## Key Files
- `README.md`: Project vision and user instructions.
- `TRADEOFFS.md`: Living document for implementation decisions.
- `src/`: Directory for source code.
- `tests/`: Directory for test suites.
- `config.json`: (Local only) Stores Gemini API keys and alignment criteria.

## Additional Coding Preferences

- Keep project dependencies small