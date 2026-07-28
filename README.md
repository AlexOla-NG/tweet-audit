# tweet-audit

Analyse your X (Twitter) archive using Gemini AI and classify tweets according to a portfolio/public-profile rubric.

## Overview

This tool processes an X archive, evaluates each tweet against your alignment criteria, and writes a structured audit report. The evaluator now uses the workspace prompt files, a scoring model, and an output schema so the classification is more explicit and easier to reason about.

## The Task

### Goal
Request an archive of your posts on X, analyse them with Google's Gemini AI, and classify tweets according to a professional-branding rubric.

### Output
A CSV file containing a structured evaluation for each tweet, including the classification label, confidence, reason, and the richer schema fields:

```csv
tweet_url,confidence,reason,label,risk_score,primary_issue,suggested_action
https://x.com/username/status/1234567890,n/a,n/a,,,,,
https://x.com/username/status/9876543210,high,Contains promotional language that may read as spammy in a professional portfolio context.,low-priority review,15,spam,review manually
```

## Setup

### 1. Request Your X Archive
Download your archive from X Settings and extract the ZIP file.

### 2. Get Gemini API Key
Visit [Google AI Studio](https://aistudio.google.com/app/apikey) and add the key to `config.json`.

## Implementation

The tool follows a batch-processing architecture with AI-driven evaluation.

### Features
- **Batch Analysis:** Processes 50 tweets at a time.
- **Checkpointing:** Resume audits from where you left off.
- **Robust Parsing:** Handles X archive's JS/JSON format.
- **Schema-Driven Evaluation:** Reads `input_prompt.md`, `scoring_model.json`, and `output_schema.json` into the prompt sent to Gemini.
- **Structured Output:** Persists label, risk score, primary issue, and suggested action into `audit_results.csv`.
- **Detailed Logging:** Operational visibility via Python logging.

### Usage

1. **Configure**: Add `gemini_api_key`, `username`, and optionally `model_name` to `config.json`.
2. **Install**: `pip install -r requirements.txt`
3. **Run**: `python main.py`
4. **Review**: Check `audit_results.csv` for the resulting classifications.

## Repository Structure
```text
tweet-audit/
├── main.py                   # Audit Engine entry point
├── src/                      # Implementation (Parser, Evaluator)
├── tests/                    # Unit tests
├── alignment_criteria.json   # Your AI rules
├── input_prompt.md           # Main evaluation instructions
├── scoring_model.json        # Risk scoring weights
├── output_schema.json        # Structured output schema
├── config.json               # Local config (ignored)
└── TRADEOFFS.md              # Architectural decisions
```

## Current Output Schema
The CSV written by the audit run contains the following columns:

- `tweet_url`: the tweet URL for the audited post
- `confidence`: the evaluator confidence (`low`, `medium`, or `high`)
- `reason`: a short explanation for the classification
- `label`: the bucket assigned by the model (`keep`, `low-priority review`, `manual review`, `archive`, or `delete`)
- `risk_score`: the numeric risk score derived from the scoring model
- `primary_issue`: the main issue category such as `tone`, `abuse`, `explicitness`, `spam`, or `political-combativeness`
- `suggested_action`: the suggested follow-up action such as `none`, `review manually`, `archive from profile`, or `delete`

## Example Alignment Criteria
```json
{
  "criteria": {
    "forbidden_words": ["crypto", "NFT"],
    "tone": "professional"
  }
}
```
