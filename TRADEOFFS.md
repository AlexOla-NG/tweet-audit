## Architecture choices (why this pattern?)
We chose a modular design with a clear separation between `ArchiveParser`, `TweetEvaluator`, and `AuditEngine`. This keeps the parsing logic, prompting logic, and batch orchestration independently testable. Python's standard `logging` and `csv` modules are used for operational transparency and structured output.

## Concurrency strategy (sequential vs batch vs full async?)
We implemented a **Batching Strategy** (50 tweets per prompt). This reduces the number of API calls while keeping the prompt compact enough for reliable evaluation. The batching approach also makes it easier to estimate token usage and rate-limit the workload.

## Error handling approach (retry? fail fast? log and continue?)
We use a **Log and Continue** approach. If a batch evaluation fails because of a network issue, malformed JSON, or a response shape mismatch, the error is logged and the engine continues with the next batch. This ensures that one bad response does not stop the entire archive audit.

## Performance vs safety trade-offs
We prioritize **Safety and Reliability** over raw speed.
- **Checkpointing:** Progress is saved to `.audit_checkpoint` after every tweet so audits can resume after interruptions without re-processing everything.
- **Rate Limiting:** We use a sliding-window `RateLimiter` to respect Gemini 3.1 Flash Lite's limits (15 RPM and 250k TPM). The engine estimates prompt size before each request and throttles execution when capacity is close to exhaustion.
- **Prompt Engineering:** The evaluator now reads `input_prompt.md`, `scoring_model.json`, and `output_schema.json` into the prompt itself so the model receives the latest rubric, scoring weights, and expected output format in a single request.
- **Structured Output:** Results are written to `audit_results.csv` with richer columns such as `label`, `risk_score`, `primary_issue`, and `suggested_action` rather than only a coarse delete flag.
- **Dual Logging:** Robust logging to `audit.log` for debugging, plus simplified console output for day-to-day runs.

## Why you chose your specific language/framework
Python was chosen for its excellent standard library (JSON/CSV handling) and the official `google-genai` SDK. We migrated to the new **`google-genai` SDK** (replacing the deprecated `google-generativeai`) and upgraded to **Gemini 3.1 Flash Lite** (from 2.5 Flash) to mitigate severe daily rate limits on the free tier. Lite provides a much higher quota while remaining capable for batch classification tasks. We implemented a custom `RateLimiter` to manage the strict 15 RPM / 250k TPM peak limits. Dependencies remain minimal (`pytest` for testing, `google-genai` for AI) so the tool stays lightweight.

