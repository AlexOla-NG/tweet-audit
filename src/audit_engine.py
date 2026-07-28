import json
import logging
import os
from typing import Dict, List

from src.evaluator import RateLimitError, TweetEvaluator
from src.parser import ArchiveParser
from src.rate_limiter import RateLimiter
from src.results_store import ResultsStore

logger = logging.getLogger("tweet-audit.main")


class AuditEngine:
    def __init__(self, config_path: str, archive_path: str, checkpoint_path: str = ".audit_checkpoint"):
        self.config_path = config_path
        self.archive_path = archive_path
        self.checkpoint_path = checkpoint_path
        self.config = self._load_config()

        with open("alignment_criteria.json", "r") as f:
            self.criteria = json.load(f)

        self.evaluator = TweetEvaluator(
            api_key=self.config["GEMINI_API_KEY"],
            criteria=self.criteria,
            model_name=self.config.get("model_name", "gemini-3.1-flash-lite"),
        )

        self.rate_limiter = RateLimiter(max_rpm=15, max_tpm=250000)
        self.results_store = ResultsStore("audit_results.csv")

    def _load_config(self) -> Dict:
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        with open(self.config_path, "r") as f:
            return json.load(f)

    def _load_checkpoint(self) -> set:
        if os.path.exists(self.checkpoint_path):
            with open(self.checkpoint_path, "r") as f:
                return set(line.strip() for line in f)
        return set()

    def _save_checkpoint(self, tweet_id: str):
        with open(self.checkpoint_path, "a") as f:
            f.write(f"{tweet_id}\n")

    def _ensure_results_store(self):
        if not hasattr(self, "results_store"):
            self.results_store = ResultsStore("audit_results.csv")

    def _migrate_csv_if_needed(self, results_file: str):
        self._ensure_results_store()
        self.results_store.results_file = results_file
        self.results_store.migrate_if_needed()

    def _get_pending_tweets(self, tweets: List[Dict], results_file: str) -> List[Dict]:
        self._ensure_results_store()
        self.results_store.results_file = results_file
        return self.results_store.get_pending_tweets(tweets)

    async def run(self, batch_size: int = 50):
        try:
            logger.info(f"Starting audit for archive: {self.archive_path}")

            parser = ArchiveParser(self.archive_path)
            all_tweets = parser.parse()

            results_file = "audit_results.csv"
            self._migrate_csv_if_needed(results_file)
            pending_tweets = self._get_pending_tweets(all_tweets, results_file)
            already_processed = len(all_tweets) - len(pending_tweets)

            logger.info(
                f"Total tweets: {len(all_tweets)}. Already processed: {already_processed}. Pending: {len(pending_tweets)}."
            )

            if not pending_tweets:
                logger.info("No pending tweets to process.")
                return

            rows_to_write = []
            for i in range(0, len(pending_tweets), batch_size):
                batch = pending_tweets[i : i + batch_size]
                logger.info(
                    f"Processing batch {i//batch_size + 1}/{(len(pending_tweets)-1)//batch_size + 1} ({len(batch)} tweets)..."
                )

                est_tokens = self.evaluator.estimate_tokens(batch)
                await self.rate_limiter.wait_for_capacity(est_tokens)

                try:
                    flagged_items, actual_tokens = await self.evaluator.evaluate_batch(batch)
                    self.rate_limiter.record_request(actual_tokens)
                    flagged_map = {item["id"]: item for item in flagged_items}
                except RateLimitError as e:
                    logger.error(f"Stopping audit due to rate limit: {e}")
                    logger.info("Progress has been saved. You can resume later.")
                    return

                for t in batch:
                    t_id = t.get("id_str") or t.get("id")
                    flagged_info = flagged_map.get(str(t_id))
                    is_flagged = flagged_info is not None
                    reason = flagged_info["reason"] if is_flagged else None
                    confidence = flagged_info["confidence"] if is_flagged else "n/a"
                    label = flagged_info.get("label") if is_flagged else ""
                    risk_score = flagged_info.get("risk_score") if is_flagged else ""
                    primary_issue = flagged_info.get("primary_issue") if is_flagged else ""
                    suggested_action = flagged_info.get("suggested_action") if is_flagged else ""

                    if is_flagged:
                        logger.warning(f"Flagged for deletion: {t_id} - Reason: {reason} - Confidence: {confidence}")

                    username = self.config.get("username", "user")
                    tweet_url = f"https://x.com/{username}/status/{t_id}"
                    rows_to_write.append(
                        {
                            "tweet_url": tweet_url,
                            "confidence": confidence,
                            "reason": reason or "n/a",
                            "label": label or "",
                            "risk_score": risk_score if risk_score is not None else "",
                            "primary_issue": primary_issue or "",
                            "suggested_action": suggested_action or "",
                        }
                    )

                    self._save_checkpoint(t_id)

            self.results_store.append_results(rows_to_write)

            logger.info("Audit complete. Results saved to audit_results.csv")
        finally:
            await self.evaluator.close()
