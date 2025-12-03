"""
API Key Management System
Phase 4: Developer API keys with usage tracking and rate limiting
"""

import logging
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class APIKey:
    """API key with metadata."""

    key_id: str
    key_hash: str
    key_prefix: str  # First 8 chars for identification
    name: str
    created_by: str
    created_at: datetime
    expires_at: Optional[datetime]
    rate_limit: int  # Requests per minute
    enabled: bool
    last_used: Optional[datetime]
    usage_count: int


class APIKeyManager:
    """Manages API keys for public API access."""

    def __init__(self, db_manager):
        """Initialize API key manager.

        Args:
            db_manager: Database manager instance
        """
        self.db = db_manager
        self._create_tables()

    def _create_tables(self):
        """Create API key management tables."""
        try:
            # API keys table
            self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id SERIAL PRIMARY KEY,
                key_id VARCHAR(100) UNIQUE NOT NULL,
                key_hash VARCHAR(64) NOT NULL,
                key_prefix VARCHAR(10) NOT NULL,
                name VARCHAR(200) NOT NULL,
                created_by VARCHAR(200),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                rate_limit INTEGER DEFAULT 60,
                enabled BOOLEAN DEFAULT TRUE,
                last_used TIMESTAMP,
                usage_count BIGINT DEFAULT 0
            )
            """)

            # API usage logs
            self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS api_usage_logs (
                id SERIAL PRIMARY KEY,
                key_id VARCHAR(100),
                endpoint VARCHAR(200),
                method VARCHAR(10),
                status_code INTEGER,
                response_time_ms INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Create indexes
            self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash)
            """)

            self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_api_usage_key_time ON api_usage_logs(key_id, timestamp)
            """)

            logger.info("API key tables created/verified")

        except Exception as e:
            logger.error(f"Error creating API key tables: {e}", exc_info=True)

    def generate_api_key(
        self, name: str, created_by: str, rate_limit: int = 60, expires_days: Optional[int] = None
    ) -> tuple[str, APIKey]:
        """Generate a new API key.

        Args:
            name: Descriptive name for the key
            created_by: Creator identifier
            rate_limit: Requests per minute
            expires_days: Days until expiration (None = never)

        Returns:
            Tuple of (api_key_string, APIKey object)
        """
        try:
            # Generate secure random key
            api_key = secrets.token_urlsafe(32)  # 32 bytes = 43 chars base64url

            # Hash for storage
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()

            # Generate unique key ID
            key_id = f"wl_{secrets.token_hex(8)}"

            # Key prefix for identification
            key_prefix = api_key[:8]

            # Calculate expiration
            expires_at = datetime.now() + timedelta(days=expires_days) if expires_days else None

            # Store in database
            query = """
            INSERT INTO api_keys
            (key_id, key_hash, key_prefix, name, created_by, expires_at, rate_limit, enabled)
            VALUES (:key_id, :key_hash, :key_prefix, :name, :created_by, :expires_at, :rate_limit, TRUE)
            RETURNING created_at
            """

            result = self.db.execute_query(
                query,
                {
                    "key_id": key_id,
                    "key_hash": key_hash,
                    "key_prefix": key_prefix,
                    "name": name,
                    "created_by": created_by,
                    "expires_at": expires_at,
                    "rate_limit": rate_limit,
                },
            )

            api_key_obj = APIKey(
                key_id=key_id,
                key_hash=key_hash,
                key_prefix=key_prefix,
                name=name,
                created_by=created_by,
                created_at=result[0]["created_at"],
                expires_at=expires_at,
                rate_limit=rate_limit,
                enabled=True,
                last_used=None,
                usage_count=0,
            )

            logger.info(f"Generated API key: {key_id} for {name}")

            # Return plaintext key (only time it's available!)
            return (api_key, api_key_obj)

        except Exception as e:
            logger.error(f"Error generating API key: {e}", exc_info=True)
            raise

    def verify_api_key(self, api_key: str) -> Optional[APIKey]:
        """Verify and retrieve API key information.

        Args:
            api_key: API key string to verify

        Returns:
            APIKey object if valid, None otherwise
        """
        try:
            # Hash the provided key
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()

            # Look up in database
            query = """
            SELECT * FROM api_keys
            WHERE key_hash = :key_hash
                AND enabled = TRUE
                AND (expires_at IS NULL OR expires_at > NOW())
            """

            results = self.db.execute_query(query, {"key_hash": key_hash})

            if not results:
                return None

            row = results[0]

            # Update last used
            self.db.execute_query(
                """
            UPDATE api_keys
            SET last_used = NOW(),
                usage_count = usage_count + 1
            WHERE key_id = :key_id
            """,
                {"key_id": row["key_id"]},
            )

            return APIKey(
                key_id=row["key_id"],
                key_hash=row["key_hash"],
                key_prefix=row["key_prefix"],
                name=row["name"],
                created_by=row["created_by"],
                created_at=row["created_at"],
                expires_at=row["expires_at"],
                rate_limit=row["rate_limit"],
                enabled=row["enabled"],
                last_used=datetime.now(),
                usage_count=row["usage_count"] + 1,
            )

        except Exception as e:
            logger.error(f"Error verifying API key: {e}", exc_info=True)
            return None

    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key.

        Args:
            key_id: Key ID to revoke

        Returns:
            True if revoked successfully
        """
        try:
            self.db.execute_query(
                """
            UPDATE api_keys
            SET enabled = FALSE
            WHERE key_id = :key_id
            """,
                {"key_id": key_id},
            )

            logger.info(f"Revoked API key: {key_id}")
            return True

        except Exception as e:
            logger.error(f"Error revoking API key: {e}", exc_info=True)
            return False

    def log_api_request(
        self, key_id: str, endpoint: str, method: str, status_code: int, response_time_ms: int
    ):
        """Log API request for analytics.

        Args:
            key_id: API key ID
            endpoint: Request endpoint
            method: HTTP method
            status_code: Response status
            response_time_ms: Response time in milliseconds
        """
        try:
            self.db.execute_query(
                """
            INSERT INTO api_usage_logs
            (key_id, endpoint, method, status_code, response_time_ms, timestamp)
            VALUES (:key_id, :endpoint, :method, :status_code, :response_time_ms, NOW())
            """,
                {
                    "key_id": key_id,
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": status_code,
                    "response_time_ms": response_time_ms,
                },
            )

        except Exception as e:
            logger.warning(f"Error logging API request: {e}")

    def get_usage_statistics(self, key_id: str, days: int = 30) -> dict:
        """Get usage statistics for an API key.

        Args:
            key_id: API key ID
            days: Days to analyze

        Returns:
            Usage statistics
        """
        try:
            query = """
            SELECT 
                COUNT(*) as total_requests,
                AVG(response_time_ms) as avg_response_time,
                MAX(response_time_ms) as max_response_time,
                COUNT(DISTINCT DATE(timestamp)) as active_days,
                COUNT(DISTINCT endpoint) as endpoints_used
            FROM api_usage_logs
            WHERE key_id = :key_id
                AND timestamp > NOW() - INTERVAL ':days days'
            """

            results = self.db.execute_query(query, {"key_id": key_id, "days": days})

            if results:
                return {
                    "total_requests": results[0]["total_requests"],
                    "avg_response_time_ms": float(results[0]["avg_response_time"])
                    if results[0]["avg_response_time"]
                    else 0,
                    "max_response_time_ms": results[0]["max_response_time"],
                    "active_days": results[0]["active_days"],
                    "endpoints_used": results[0]["endpoints_used"],
                    "period_days": days,
                }

            return {}

        except Exception as e:
            logger.error(f"Error getting usage stats: {e}", exc_info=True)
            return {}


# Singleton
_api_key_manager: Optional[APIKeyManager] = None


def get_api_key_manager(db_manager) -> APIKeyManager:
    """Get or create API key manager instance."""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager(db_manager)
    return _api_key_manager
