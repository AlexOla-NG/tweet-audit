import csv
import os
from typing import Dict, List

RESULT_COLUMNS = [
    "tweet_url",
    "confidence",
    "reason",
    "label",
    "risk_score",
    "primary_issue",
    "suggested_action",
]


class ResultsStore:
    def __init__(self, results_file: str = "audit_results.csv"):
        self.results_file = results_file

    def migrate_if_needed(self):
        """Checks if the existing results CSV has the old schema and migrates it."""
        if not os.path.exists(self.results_file):
            return

        with open(self.results_file, "r", newline="", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            try:
                headers = next(reader)
            except StopIteration:
                headers = []

        if headers and "confidence" not in headers:
            temp_file = self.results_file + ".tmp"
            with open(self.results_file, "r", newline="", encoding="utf-8") as infile, open(temp_file, "w", newline="", encoding="utf-8") as outfile:
                reader = csv.DictReader(infile)
                writer = csv.DictWriter(outfile, fieldnames=RESULT_COLUMNS)
                writer.writeheader()

                for row in reader:
                    writer.writerow(
                        {
                            "tweet_url": row.get("tweet_url"),
                            "confidence": row.get("confidence") or "n/a",
                            "reason": row.get("reason"),
                            "label": "",
                            "risk_score": "",
                            "primary_issue": "",
                            "suggested_action": "",
                        }
                    )

            os.replace(temp_file, self.results_file)

    def get_pending_tweets(self, tweets: List[Dict]) -> List[Dict]:
        """Return tweets that still need evaluation based on the results CSV state."""
        if not os.path.exists(self.results_file):
            return tweets

        processed_ids = set()
        with open(self.results_file, "r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                tweet_url = (row.get("tweet_url") or "").strip()
                if not tweet_url:
                    continue

                tweet_id = tweet_url.split("/status/")[-1].split("?")[0].split("#")[0]
                if not tweet_id:
                    continue

                confidence = (row.get("confidence") or "").strip()
                if confidence:
                    processed_ids.add(tweet_id)

        return [tweet for tweet in tweets if str(tweet.get("id_str") or tweet.get("id")) not in processed_ids]

    def append_results(self, rows: List[Dict]):
        file_exists = os.path.exists(self.results_file)
        with open(self.results_file, "a", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=RESULT_COLUMNS)
            if not file_exists:
                writer.writeheader()
            writer.writerows(rows)
