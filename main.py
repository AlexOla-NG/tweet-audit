import asyncio

from src.audit_engine import AuditEngine
from src.logging_setup import configure_logging


if __name__ == "__main__":
    configure_logging()

    # Default paths based on project structure
    ARCHIVE_FILE = "twitter-data-2026-06-11/data/tweets.js"
    engine = AuditEngine("config.json", ARCHIVE_FILE)
    asyncio.run(engine.run())
