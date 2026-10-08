"""
Mock Redis client for NexusCX Orchestration Engine.
"""
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

class MockRedisClient:
    """Mock Redis client for testing purposes."""

    def __init__(self):
        self.data = {}
        logger.info("Mock Redis client initialized")

    async def get(self, key: str) -> Optional[str]:
        """Get a value from the mock Redis."""
        return self.data.get(key)

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set a value in the mock Redis."""
        self.data[key] = value
        return True

    async def delete(self, key: str) -> int:
        """Delete a key from the mock Redis."""
        if key in self.data:
            del self.data[key]
            return 1
        return 0

    async def exists(self, key: str) -> bool:
        """Check if a key exists in the mock Redis."""
        return key in self.data

# Global mock Redis client instance
redis_client = MockRedisClient()