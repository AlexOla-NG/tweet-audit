import asyncio
import logging
import time
from collections import deque
from typing import Deque

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
        while self.requests and now - self.requests[0] > 60:
            self.requests.popleft()
        while self.tokens and now - self.tokens[0][0] > 60:
            self.tokens.popleft()

    async def wait_for_capacity(self, estimated_tokens: int):
        """Waits until there is capacity for another request with estimated tokens."""
        while True:
            self._clean_windows()

            current_rpm = len(self.requests)
            current_tpm = sum(token_count for _, token_count in self.tokens)

            if current_rpm < self.max_rpm and (current_tpm + estimated_tokens) < self.max_tpm:
                break

            logger.info(
                f"Rate limit approaching (RPM: {current_rpm}/{self.max_rpm}, TPM: {current_tpm}/{self.max_tpm}). Throttling..."
            )
            await asyncio.sleep(2)

    def record_request(self, actual_tokens: int):
        """Records a successful request and its token usage."""
        now = time.time()
        self.requests.append(now)
        self.tokens.append((now, actual_tokens))
