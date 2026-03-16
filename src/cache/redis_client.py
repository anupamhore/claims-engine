"""
WHY: Redis caching layer for performance optimization
  - Sub-millisecond BERT inference caching (100-200ms → <1ms)
  - Session management for Streamlit users
  - Real-time aggregation caches (fraud rates, claim counts)
  - Feature store for streaming features (Kafka → Redis)

HOW:
  - JSON serialization for complex objects
  - TTL-based expiration (24h for predictions, 1h for sessions)
  - Connection pooling for efficiency

ALTERNATIVE not chosen:
  - Memcached: No persistence, less flexible data types
  - In-memory Python dict: Single process only, not scalable
"""

import redis
import json
import os
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

# Redis configuration from .env
# In Docker: REDIS_HOST will be 'redis' (service name)
# In Local: REDIS_HOST will be 'localhost' (Homebrew installation)
# The code works the same way - it just connects to different hosts!
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_TTL = int(os.getenv("REDIS_TTL", "86400"))  # Default 24 hours

# Create Redis connection pool
# Docker: Connects to 'redis' service
# Local:  Connects to localhost
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=True,  # Return strings instead of bytes
    socket_connect_timeout=5,
    socket_keepalive=True,
    health_check_interval=30,
)


class CacheManager:
    """
    Centralized cache management with TTL and serialization.
    
    Usage:
        # Cache BERT embedding
        cache.set_with_ttl("bert:claim_123", embedding, ttl=86400)
        
        # Get cached value
        cached = cache.get("bert:claim_123")
        
        # Cache fraud score
        cache.set("fraud:claim_123", fraud_score_dict, ttl=3600)
    """

    @staticmethod
    def get(key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = redis_client.get(key)
            if value:
                # Try to deserialize as JSON
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    # Return raw string if not JSON
                    return value
            return None
        except redis.ConnectionError as e:
            logger.warning(f"Redis connection error on GET {key}: {e}")
            return None

    @staticmethod
    def set(key: str, value: Any, ttl: int = REDIS_TTL) -> bool:
        """Set value in cache with TTL."""
        try:
            # Serialize to JSON if dict/list
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            redis_client.setex(key, ttl, value)
            return True
        except redis.ConnectionError as e:
            logger.warning(f"Redis connection error on SET {key}: {e}")
            return False

    @staticmethod
    def delete(key: str) -> bool:
        """Delete key from cache."""
        try:
            redis_client.delete(key)
            return True
        except redis.ConnectionError as e:
            logger.warning(f"Redis connection error on DELETE {key}: {e}")
            return False

    @staticmethod
    def exists(key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return redis_client.exists(key) > 0
        except redis.ConnectionError as e:
            logger.warning(f"Redis connection error on EXISTS {key}: {e}")
            return False

    @staticmethod
    def flush_all() -> bool:
        """Flush all keys (dangerous - use in tests only)."""
        try:
            redis_client.flushall()
            return True
        except redis.ConnectionError as e:
            logger.warning(f"Redis connection error on FLUSHALL: {e}")
            return False

    @staticmethod
    def get_stats() -> dict:
        """Get Redis stats for monitoring."""
        try:
            info = redis_client.info()
            return {
                "connected_clients": info.get("connected_clients"),
                "used_memory_mb": info.get("used_memory") / (1024 * 1024),
                "evicted_keys": info.get("evicted_keys"),
                "total_commands_processed": info.get("total_commands_processed"),
            }
        except redis.ConnectionError as e:
            logger.warning(f"Redis connection error on INFO: {e}")
            return {}


# Specific cache key patterns
class CacheKeys:
    """
    Centralized cache key naming to avoid collisions.
    
    Why: Makes keys consistent and easy to find in Redis
    """
    
    # BERT embeddings: bert:{claim_id}
    @staticmethod
    def bert_embedding(claim_id: int) -> str:
        return f"bert:{claim_id}"

    # Fraud scores: fraud:{claim_id}
    @staticmethod
    def fraud_score(claim_id: int) -> str:
        return f"fraud:{claim_id}"

    # LLM explanations: explanation:{claim_id}
    @staticmethod
    def explanation(claim_id: int) -> str:
        return f"explanation:{claim_id}"

    # User sessions: session:{user_id}
    @staticmethod
    def user_session(user_id: str) -> str:
        return f"session:{user_id}"

    # Real-time stats: stats:{metric_name}
    @staticmethod
    def stats(metric: str) -> str:
        return f"stats:{metric}"

    # Feature store: features:{claim_id}
    @staticmethod
    def features(claim_id: int) -> str:
        return f"features:{claim_id}"


def check_redis_connection() -> bool:
    """Check if Redis is accessible."""
    try:
        redis_client.ping()
        logger.info("✅ Redis connection successful")
        return True
    except redis.ConnectionError as e:
        logger.error(f"❌ Redis connection failed: {e}")
        return False
