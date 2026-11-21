"""MongoDB connection and chat history persistence for SchemeSaathi.

Uses Motor for asynchronous operations with an in-memory fallback cache
when MongoDB is not running, ensuring zero downtime during local development.
"""

from datetime import datetime
import logging
from typing import Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import get_settings
from app.models import ChatHistoryMessage, ChatSessionHistory

logger = logging.getLogger("schemesaathi.db")

# Global database client state
_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None

# In-memory fallback session store when MongoDB is offline
_in_memory_sessions: Dict[str, ChatSessionHistory] = {}


async def connect_to_mongo() -> None:
    """Initialize MongoDB connection pool."""
    global _client, _db
    settings = get_settings()
    try:
        _client = AsyncIOMotorClient(
            settings.MONGO_URI,
            serverSelectionTimeoutMS=1500,
        )
        _db = _client[settings.MONGO_DB_NAME]
        # Quick ping to verify connectivity
        await _client.admin.command("ping")
        logger.info("Successfully connected to MongoDB (%s)", settings.MONGO_DB_NAME)
    except Exception as exc:
        logger.warning(
            "MongoDB unavailable at %s (%s). Falling back to in-memory session cache.",
            settings.MONGO_URI,
            exc,
        )
        _client = None
        _db = None


async def close_mongo_connection() -> None:
    """Close MongoDB connection pool on shutdown."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed.")


def get_db() -> Optional[AsyncIOMotorDatabase]:
    """Retrieve active MongoDB database instance."""
    return _db


async def check_mongo_health() -> bool:
    """Verify if MongoDB is currently reachable."""
    if _client is None:
        return False
    try:
        await _client.admin.command("ping")
        return True
    except Exception:
        return False


async def save_chat_message(
    session_id: str,
    user_query: str,
    assistant_response: str,
    sources: Optional[list] = None,
) -> bool:
    """Save user and assistant message pair to MongoDB or in-memory fallback."""
    now = datetime.utcnow()
    user_msg = ChatHistoryMessage(role="user", content=user_query, timestamp=now)
    assistant_msg = ChatHistoryMessage(
        role="assistant",
        content=assistant_response,
        sources=sources or [],
        timestamp=now,
    )

    db = get_db()
    if db is not None:
        try:
            collection = db["chat_sessions"]
            await collection.update_one(
                {"session_id": session_id},
                {
                    "$push": {
                        "messages": {
                            "$each": [user_msg.model_dump(), assistant_msg.model_dump()]
                        }
                    },
                    "$setOnInsert": {"created_at": now},
                    "$set": {"updated_at": now},
                },
                upsert=True,
            )
            return True
        except Exception as exc:
            logger.error("Failed to persist messages to MongoDB: %s", exc)

    # Fallback to in-memory store
    if session_id not in _in_memory_sessions:
        _in_memory_sessions[session_id] = ChatSessionHistory(
            session_id=session_id,
            messages=[],
            created_at=now,
            updated_at=now,
        )
    session = _in_memory_sessions[session_id]
    session.messages.extend([user_msg, assistant_msg])
    session.updated_at = now
    return True


async def get_session_history(session_id: str) -> Optional[ChatSessionHistory]:
    """Fetch session history messages by session ID from MongoDB or in-memory store."""
    db = get_db()
    if db is not None:
        try:
            doc = await db["chat_sessions"].find_one({"session_id": session_id})
            if doc:
                return ChatSessionHistory(**doc)
        except Exception as exc:
            logger.error("Error reading session %s from MongoDB: %s", session_id, exc)

    # Check in-memory store
    return _in_memory_sessions.get(session_id)


async def delete_session_history(session_id: str) -> bool:
    """Delete chat history for a session from MongoDB and in-memory store."""
    deleted = False
    db = get_db()
    if db is not None:
        try:
            result = await db["chat_sessions"].delete_one({"session_id": session_id})
            if result.deleted_count > 0:
                deleted = True
        except Exception as exc:
            logger.error("Error deleting session %s from MongoDB: %s", session_id, exc)

    if session_id in _in_memory_sessions:
        del _in_memory_sessions[session_id]
        deleted = True

    return deleted
