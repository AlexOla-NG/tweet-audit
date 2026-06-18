## Architecture choices (why this pattern?)
We chose a modular design with a clear separation between `ArchiveParser`, `TweetEvaluator`, and `AuditEngine`. This allows for independent testing of the parsing logic and AI interaction. Python's standard `logging` library is used for operational transparency.

## Concurrency strategy (sequential vs batch vs full async?)
We implemented a **Batching Strategy** (20-50 tweets per prompt). This optimizes token usage and significantly reduces the number of API calls, preventing us from hitting "Requests Per Minute" limits while maintaining high throughput.

## Error handling approach (retry? fail fast? log and continue?)
We use a **Log and Continue** approach. If a batch evaluation fails due to network or JSON parsing issues, the error is logged, and the engine moves to the next batch. This ensures that one faulty API response doesn't halt the entire audit of the archive.

## Performance vs safety trade-offs
We prioritize **Safety and Reliability** over raw speed.
- **Checkpointing:** Progress is saved to `.audit_checkpoint` after every tweet. This allows resuming after interruptions without double-spending tokens.
- **Rate Limiting:** We use a sophisticated **Sliding Window Rate Limiter** to strictly respect Gemini 3.1 Flash Lite's constraints (15 RPM and 250k TPM). The engine estimates token usage before each request and throttles execution (via `asyncio.sleep`) if capacity is reached, ensuring we never trigger 429 errors during long-running audits. Actual token usage from API responses is used to maintain precision.
- **Dual Logging:** Robust logging to `audit.log` for debugging, and simplified output to the console for a cleaner user experience.

## Why you chose your specific language/framework
Python was chosen for its excellent standard library (JSON/CSV handling) and the official `google-genai` SDK. We migrated to the new **`google-genai` SDK** (replacing the deprecated `google-generativeai`) and upgraded to **Gemini 3.1 Flash Lite** (from 2.5 Flash) to mitigate severe daily rate limits on the free tier. Lite provides a much higher quota (500 requests/day vs 20) while remaining capable for batch classification tasks. We implemented a custom `RateLimiter` to manage the strict 15 RPM / 250k TPM peak limits. We kept dependencies minimal (`pytest` for testing, `google-genai` for AI) to ensure the tool remains lightweight.
