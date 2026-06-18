## Architecture choices (why this pattern?)
We chose a modular design with a clear separation between `ArchiveParser`, `TweetEvaluator`, and `AuditEngine`. This allows for independent testing of the parsing logic and AI interaction. Python's standard `logging` library is used for operational transparency.

## Concurrency strategy (sequential vs batch vs full async?)
We implemented a **Batching Strategy** (20-50 tweets per prompt). This optimizes token usage and significantly reduces the number of API calls, preventing us from hitting "Requests Per Minute" limits while maintaining high throughput.

## Error handling approach (retry? fail fast? log and continue?)
We use a **Log and Continue** approach. If a batch evaluation fails due to network or JSON parsing issues, the error is logged, and the engine moves to the next batch. This ensures that one faulty API response doesn't halt the entire audit of the archive.

## Performance vs safety trade-offs
We prioritize **Safety and Reliability** over raw speed.
- **Checkpointing:** Progress is saved to `.audit_checkpoint` after every tweet. This allows resuming after interruptions without double-spending tokens.
- **Rate Limiting:** A 1-second delay is added between batches to stay well within Gemini API limits.
- **Dual Logging:** Robust logging to `audit.log` for debugging, and simplified output to the console for a cleaner user experience.

## Why you chose your specific language/framework
Python was chosen for its excellent standard library (JSON/CSV handling) and the official `google-genai` SDK. We migrated to the new **`google-genai` SDK** (replacing the deprecated `google-generativeai`) and upgraded to **Gemini 2.5 Flash** for improved performance and long-term support. We kept dependencies minimal (`pytest` for testing, `google-genai` for AI) to ensure the tool remains lightweight.
