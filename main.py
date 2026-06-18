import asyncio
import csv
import json
import logging
import os
import time
from typing import List, Dict, Deque
from collections import deque
from src.parser import ArchiveParser
from src.evaluator import TweetEvaluator, RateLimitError

# Configure logging to both file and console with different formats
log_formatter_file = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_formatter_console = logging.Formatter('[%(levelname)s] %(message)s')

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# File handler: robust logging
file_handler = logging.FileHandler("audit.log")
file_handler.setFormatter(log_formatter_file)
root_logger.addHandler(file_handler)

# Console handler: simple logging
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter_console)
root_logger.addHandler(console_handler)

logger = logging.getLogger("tweet-audit.main")

class RateLimiter:
    """Sliding window rate limiter for RPM and TPM."""
    def __init__(self, max_rpm: int = 15, max_tpm: int = 250000):
        self.max_rpm = max_rpm
        self.max_tpm = max_tpm
        self.requests: Deque[float] = deque()
        self.tokens: Deque[tuple[float, int]] = deque()

    def _clean_windows(self):
        now = time.time()
        # Keep only last 60 seconds
        while self.requests and now - self.requests[0] > 60:
            self.requests.popleft()
        while self.tokens and now - self.tokens[0][0] > 60:
            self.tokens.popleft()

    async def wait_for_capacity(self, estimated_tokens: int):
        """Waits until there is capacity for another request with estimated tokens."""
        while True:
            self._clean_windows()
            
            current_rpm = len(self.requests)
            current_tpm = sum(t[1] for t in self.tokens)
            
            if current_rpm < self.max_rpm and (current_tpm + estimated_tokens) < self.max_tpm:
                break
                
            # Wait a bit before checking again
            logger.info(f"Rate limit approaching (RPM: {current_rpm}/{self.max_rpm}, TPM: {current_tpm}/{self.max_tpm}). Throttling...")
            await asyncio.sleep(2)

    def record_request(self, actual_tokens: int):
        """Records a successful request and its token usage."""
        now = time.time()
        self.requests.append(now)
        self.tokens.append((now, actual_tokens))

class AuditEngine:
    def __init__(self, config_path: str, archive_path: str, checkpoint_path: str = ".audit_checkpoint"):
        self.config_path = config_path
        self.archive_path = archive_path
        self.checkpoint_path = checkpoint_path
        self.config = self._load_config()
        
        # Load alignment criteria
        with open("alignment_criteria.json", "r") as f:
            self.criteria = json.load(f)
            
        self.evaluator = TweetEvaluator(
            api_key=self.config["GEMINI_API_KEY"],
            criteria=self.criteria,
            model_name=self.config.get("model_name", "gemini-3.1-flash-lite")
        )
        
        # Initialize RateLimiter for Gemini 3.1 Flash Lite
        self.rate_limiter = RateLimiter(max_rpm=15, max_tpm=250000)

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

    async def run(self, batch_size: int = 50):
        try:
            logger.info(f"Starting audit for archive: {self.archive_path}")
            
            parser = ArchiveParser(self.archive_path)
            all_tweets = parser.parse()
            processed_ids = self._load_checkpoint()
            
            # Filter out already processed tweets
            pending_tweets = [t for t in all_tweets if (t.get("id_str") or t.get("id")) not in processed_ids]
            
            logger.info(f"Total tweets: {len(all_tweets)}. Already processed: {len(processed_ids)}. Pending: {len(pending_tweets)}.")
            
            if not pending_tweets:
                logger.info("No pending tweets to process.")
                return

            results_file = "audit_results.csv"
            file_exists = os.path.exists(results_file)
            
            with open(results_file, "a", newline="") as csvfile:
                fieldnames = ["tweet_url", "deleted", "reason"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                if not file_exists:
                    writer.writeheader()

                for i in range(0, len(pending_tweets), batch_size):
                    batch = pending_tweets[i : i + batch_size]
                    logger.info(f"Processing batch {i//batch_size + 1}/{(len(pending_tweets)-1)//batch_size + 1} ({len(batch)} tweets)...")
                    
                    # Estimate tokens and wait if necessary
                    est_tokens = self.evaluator.estimate_tokens(batch)
                    await self.rate_limiter.wait_for_capacity(est_tokens)
                    
                    try:
                        flagged_items, actual_tokens = await self.evaluator.evaluate_batch(batch)
                        self.rate_limiter.record_request(actual_tokens)
                        
                        # Create a map for quick lookup
                        reason_map = {item["id"]: item["reason"] for item in flagged_items}
                    except RateLimitError as e:
                        logger.error(f"Stopping audit due to rate limit: {e}")
                        logger.info("Progress has been saved. You can resume later.")
                        return

                    for t in batch:
                        t_id = t.get("id_str") or t.get("id")
                        reason = reason_map.get(str(t_id))
                        is_flagged = reason is not None
                        
                        # Log flagged tweets
                        if is_flagged:
                            logger.warning(f"Flagged for deletion: {t_id} - Reason: {reason}")
                        
                        # Write to CSV
                        username = self.config.get("username", "user")
                        tweet_url = f"https://x.com/{username}/status/{t_id}"
                        writer.writerow({
                            "tweet_url": tweet_url, 
                            "deleted": "true" if is_flagged else "false",
                            "reason": reason or "n/a"
                        })
                        
                        # Mark as processed
                        self._save_checkpoint(t_id)

            logger.info("Audit complete. Results saved to audit_results.csv")
        finally:
            await self.evaluator.close()

if __name__ == "__main__":
    # Default paths based on project structure
    ARCHIVE_FILE = "twitter-data-2026-06-11/data/tweets.js"
    engine = AuditEngine("config.json", ARCHIVE_FILE)
    asyncio.run(engine.run())
