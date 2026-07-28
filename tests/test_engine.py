import os
import csv
from unittest.mock import patch
from main import AuditEngine

def test_migrate_csv_if_needed_old_schema(tmp_path):
    with patch.object(AuditEngine, '__init__', lambda self: None):
        engine = AuditEngine()
        
        # Create a temp csv file with the old schema
        old_csv = tmp_path / "audit_results.csv"
        with open(old_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["tweet_url", "deleted", "reason"])
            writer.writerow(["https://x.com/user/status/1", "true", "offensive"])
            writer.writerow(["https://x.com/user/status/2", "false", "n/a"])
            
        engine._migrate_csv_if_needed(str(old_csv))
        
        # Read back and verify the migrated contents
        with open(old_csv, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert reader.fieldnames == [
            "tweet_url",
            "confidence",
            "reason",
            "label",
            "risk_score",
            "primary_issue",
            "suggested_action",
        ]
        assert len(rows) == 2
        assert rows[0] == {
            "tweet_url": "https://x.com/user/status/1",
            "confidence": "n/a",
            "reason": "offensive",
            "label": "",
            "risk_score": "",
            "primary_issue": "",
            "suggested_action": "",
        }
        assert rows[1] == {
            "tweet_url": "https://x.com/user/status/2",
            "confidence": "n/a",
            "reason": "n/a",
            "label": "",
            "risk_score": "",
            "primary_issue": "",
            "suggested_action": "",
        }

def test_migrate_csv_if_needed_already_new_schema(tmp_path):
    with patch.object(AuditEngine, '__init__', lambda self: None):
        engine = AuditEngine()
        
        new_csv = tmp_path / "audit_results.csv"
        with open(new_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["tweet_url", "deleted", "confidence", "reason"])
            writer.writerow(["https://x.com/user/status/1", "true", "High", "offensive"])
            
        # Get modification time to check if file was rewritten
        initial_mtime = os.path.getmtime(new_csv)
        
        engine._migrate_csv_if_needed(str(new_csv))
        
        with open(new_csv, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert reader.fieldnames == [
            "tweet_url",
            "deleted",
            "confidence",
            "reason",
        ]
        assert len(rows) == 1
        assert rows[0] == {
            "tweet_url": "https://x.com/user/status/1",
            "deleted": "true",
            "confidence": "High",
            "reason": "offensive"
        }

def test_migrate_csv_if_needed_no_file():
    with patch.object(AuditEngine, '__init__', lambda self: None):
        engine = AuditEngine()
        # Should not raise any error if file doesn't exist
        engine._migrate_csv_if_needed("non_existent_file.csv")


def test_get_pending_tweets_uses_results_csv_state(tmp_path):
    with patch.object(AuditEngine, '__init__', lambda self: None):
        engine = AuditEngine()

        results_file = tmp_path / "audit_results.csv"
        with open(results_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["tweet_url", "deleted", "confidence", "reason"])
            writer.writeheader()
            writer.writerow({
                "tweet_url": "https://x.com/user/status/1",
                "deleted": "true",
                "confidence": "High",
                "reason": "offensive"
            })
            writer.writerow({
                "tweet_url": "https://x.com/user/status/2",
                "deleted": "true",
                "confidence": "",
                "reason": "spam"
            })

        tweets = [{"id": "1"}, {"id": "2"}, {"id": "3"}]
        pending = engine._get_pending_tweets(tweets, str(results_file))

        assert [tweet["id"] for tweet in pending] == ["2", "3"]


def test_get_pending_tweets_when_results_csv_missing(tmp_path):
    with patch.object(AuditEngine, '__init__', lambda self: None):
        engine = AuditEngine()

        results_file = tmp_path / "audit_results.csv"
        tweets = [{"id": "1"}, {"id": "2"}]
        pending = engine._get_pending_tweets(tweets, str(results_file))

        assert [tweet["id"] for tweet in pending] == ["1", "2"]
