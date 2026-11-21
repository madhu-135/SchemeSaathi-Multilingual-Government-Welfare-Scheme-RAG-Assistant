"""Main FastAPI application entry point for SchemeSaathi.

Provides RESTful endpoints for RAG chat querying, conversation history management,
scheme discovery, and health checks with slowapi rate limiting and structured logging.
"""

from contextlib import asynccontextmanager
import logging
import time
from typing import List
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import get_settings
from app.db import (
    check_mongo_health,
    close_mongo_connection,
    connect_to_mongo,
    delete_session_history,
    get_session_history,
    save_chat_message,
)
from app.models import (
    ChatRequest,
    ChatResponse,
    ChatSessionHistory,
    DeleteHistoryResponse,
    HealthResponse,
    SchemesResponse,
    SourceCitation,
)
from app.rag import answer
from app.vectorstore import get_vector_store

# Configure structured application logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("schemesaathi.api")

# Initialize SlowAPI rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown routines."""
    logger.info("Starting up SchemeSaathi API server...")
    settings = get_settings()
    settings.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    settings.INDEX_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize MongoDB connection
    await connect_to_mongo()

    yield

    # Clean up MongoDB connection pool on shutdown
    await close_mongo_connection()
    logger.info("SchemeSaathi API server shut down.")


settings = get_settings()
app = FastAPI(
    title="SchemeSaathi API",
    description="Multilingual (English & Tamil) RAG Chatbot for Indian Government Schemes",
    version="0.1.0",
    lifespan=lifespan,
)

# Register SlowAPI rate limiter state and error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS Middleware for React frontend dev servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# Health Check Endpoint
# ==============================================================================

@app.get(
    "/health",
    response_model=HealthResponse,
    summary="System Health & Status Check",
    tags=["System"],
)
async def health_check() -> HealthResponse:
    """Check backend operational health, MongoDB reachability, and index size."""
    mongo_ok = await check_mongo_health()
    vector_store = get_vector_store()
    total_docs = vector_store.total_documents

    status_val = "healthy" if mongo_ok else "degraded"

    return HealthResponse(
        status=status_val,
        app_name="SchemeSaathi",
        version="0.1.0",
        embedding_model=settings.EMBED_MODEL,
        mongo_connected=mongo_ok,
        indexed_documents_count=total_docs,
    )


# ==============================================================================
# Chat Endpoint (POST /chat) with Rate Limiting & Structured Logging
# ==============================================================================

@app.post(
    "/chat",
    response_model=ChatResponse,
    summary="Submit question and generate grounded RAG answer",
    tags=["Chat"],
)
@app.post(
    "/api/chat",
    response_model=ChatResponse,
    include_in_schema=False,
    tags=["Chat"],
)
@limiter.limit("30/minute")
async def chat_endpoint(request: Request, payload: ChatRequest) -> ChatResponse:
    """Answer question about government schemes in English or Tamil.

    Retrieves top chunks, filters by similarity threshold, generates an answer
    grounded strictly in context, logs latency and retrieved chunk IDs, and persists
    the conversation turn to MongoDB.
    """
    start_time = time.perf_counter()

    # 1. Fetch prior conversation history for context
    history_record = await get_session_history(payload.session_id)
    history_messages = history_record.messages if history_record else []

    # 2. Invoke RAG pipeline
    result = await answer(
        question=payload.question,
        history=history_messages,
        scheme_filter=payload.scheme_filter,
    )

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    # 3. Extract chunk IDs and format citations
    sources_data = result.get("sources", [])
    chunk_ids = []
    citations: List[SourceCitation] = []

    # Correlate source citations with vectorstore chunk IDs
    vector_store = get_vector_store()
    for src in sources_data:
        chunk_name = src.get("scheme_name", "")
        page_num = src.get("page_number", 0)
        # Match chunk_id from vector store
        matched_id = next(
            (
                c.chunk_id
                for c in vector_store.chunks
                if c.scheme_name == chunk_name and c.page_number == page_num
            ),
            f"{chunk_name.lower().replace(' ', '_')}_p{page_num}",
        )
        chunk_ids.append(matched_id)

        citations.append(
            SourceCitation(
                scheme_name=src["scheme_name"],
                source_file=src["source_file"],
                page_number=src["page_number"],
                score=src["score"],
                snippet=src["snippet"],
            )
        )

    # 4. Structured logging of latency and retrieved chunk IDs
    logger.info(
        "CHAT_EVENT status=success session_id=%s latency_ms=%.2f language=%s chunks_count=%d chunk_ids=%s query=\"%s\"",
        payload.session_id,
        elapsed_ms,
        result["language"],
        len(chunk_ids),
        chunk_ids,
        payload.question[:80].replace("\n", " "),
    )

    # 5. Persist turn to MongoDB (or in-memory cache)
    sources_dict = [c.model_dump() for c in citations]
    await save_chat_message(
        session_id=payload.session_id,
        user_query=payload.question,
        assistant_response=result["answer"],
        sources=sources_dict,
    )

    return ChatResponse(
        session_id=payload.session_id,
        question=payload.question,
        answer=result["answer"],
        language=result["language"],
        sources=citations,
        chunk_ids=chunk_ids,
        latency_ms=round(elapsed_ms, 2),
    )


# ==============================================================================
# History Endpoints (GET & DELETE /history/{session_id})
# ==============================================================================

@app.get(
    "/history/{session_id}",
    response_model=ChatSessionHistory,
    summary="Retrieve conversation history for a session",
    tags=["Chat"],
)
@app.get(
    "/api/history/{session_id}",
    response_model=ChatSessionHistory,
    include_in_schema=False,
    tags=["Chat"],
)
async def get_history(session_id: str) -> ChatSessionHistory:
    """Fetch all messages for the specified session ID."""
    history = await get_session_history(session_id)
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No chat history found for session_id '{session_id}'.",
        )
    return history


@app.delete(
    "/history/{session_id}",
    response_model=DeleteHistoryResponse,
    summary="Clear conversation history for a session",
    tags=["Chat"],
)
@app.delete(
    "/api/history/{session_id}",
    response_model=DeleteHistoryResponse,
    include_in_schema=False,
    tags=["Chat"],
)
async def clear_history(session_id: str) -> DeleteHistoryResponse:
    """Delete all recorded messages for the specified session ID."""
    deleted = await delete_session_history(session_id)
    if not deleted:
        return DeleteHistoryResponse(
            session_id=session_id,
            deleted=False,
            message=f"Session '{session_id}' did not exist or had no messages.",
        )

    logger.info("SESSION_DELETED session_id=%s", session_id)
    return DeleteHistoryResponse(
        session_id=session_id,
        deleted=True,
        message=f"Chat history for session '{session_id}' was successfully cleared.",
    )


# ==============================================================================
# Schemes Discovery Endpoint (GET /schemes)
# ==============================================================================

@app.get(
    "/schemes",
    response_model=SchemesResponse,
    summary="List all indexed government schemes",
    tags=["Schemes"],
)
async def list_schemes() -> SchemesResponse:
    """Retrieve distinct scheme names and count available in the vector store."""
    vector_store = get_vector_store()
    unique_schemes = sorted(list({c.scheme_name for c in vector_store.chunks}))
    return SchemesResponse(
        schemes=unique_schemes,
        total_count=len(unique_schemes),
    )


@app.get(
    "/api/schemes",
    response_model=List[str],
    include_in_schema=False,
    tags=["Schemes"],
)
async def list_schemes_api() -> List[str]:
    """Array of distinct scheme names for frontend dropdown selection."""
    vector_store = get_vector_store()
    return sorted(list({c.scheme_name for c in vector_store.chunks}))
