import asyncio
import csv
import json
import logging
import os
from typing import List, Dict
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
            model_name=self.config.get("model_name", "gemini-2.0-flash-lite")
        )

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
                fieldnames = ["tweet_url", "deleted"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                if not file_exists:
                    writer.writeheader()

                for i in range(0, len(pending_tweets), batch_size):
                    batch = pending_tweets[i : i + batch_size]
                    logger.info(f"Processing batch {i//batch_size + 1}/{(len(pending_tweets)-1)//batch_size + 1} ({len(batch)} tweets)...")
                    
                    try:
                        flagged_ids = await self.evaluator.evaluate_batch(batch)
                    except RateLimitError as e:
                        logger.error(f"Stopping audit due to rate limit: {e}")
                        logger.info("Progress has been saved. You can resume later.")
                        return

                    for t in batch:
                        t_id = t.get("id_str") or t.get("id")
                        is_flagged = t_id in flagged_ids
                        
                        # Log flagged tweets
                        if is_flagged:
                            logger.warning(f"Flagged for deletion: {t_id}")
                        
                        # Write to CSV
                        username = self.config.get("username", "user")
                        tweet_url = f"https://x.com/{username}/status/{t_id}"
                        writer.writerow({"tweet_url": tweet_url, "deleted": "false" if is_flagged else "n/a"})
                        
                        # Mark as processed
                        self._save_checkpoint(t_id)
                    
                    # Simple rate limiting to be safe
                    await asyncio.sleep(1)

            logger.info("Audit complete. Results saved to audit_results.csv")
        finally:
            await self.evaluator.close()

if __name__ == "__main__":
    # Default paths based on project structure
    ARCHIVE_FILE = "twitter-data-2026-06-11/data/tweets.js"
    engine = AuditEngine("config.json", ARCHIVE_FILE)
    asyncio.run(engine.run())
