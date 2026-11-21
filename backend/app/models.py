"""Pydantic data models and schemas for SchemeSaathi API."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# ==============================================================================
# Health Check Models
# ==============================================================================

class HealthResponse(BaseModel):
    """Health check response schema."""
    status: Literal["healthy", "degraded", "unhealthy"] = "healthy"
    app_name: str = "SchemeSaathi"
    version: str = "0.1.0"
    embedding_model: str
    mongo_connected: bool
    indexed_documents_count: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ==============================================================================
# Document & Ingestion Models
# ==============================================================================

class DocumentChunk(BaseModel):
    """Represents a text chunk extracted from a scheme PDF document."""
    chunk_id: str
    scheme_name: str
    source_file: str
    language: Literal["en", "ta", "auto"] = "auto"
    page_number: int
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IngestionStats(BaseModel):
    """Summary statistics for a PDF ingestion run."""
    total_files_processed: int
    total_pages_extracted: int
    total_chunks_created: int
    processed_files: List[str]
    errors: List[str] = Field(default_factory=list)


# ==============================================================================
# RAG & Chat Models
# ==============================================================================

class SourceCitation(BaseModel):
    """Source reference for RAG generation."""
    scheme_name: str
    source_file: str
    page_number: int
    score: float
    snippet: str


class ChatRequest(BaseModel):
    """User chat request payload with validation."""
    session_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Unique session identifier for chat history tracking",
        example="session_user_123",
    )
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Citizen question in English or Tamil (தமிழ்)",
        example="What is the financial assistance provided under PM Kisan?",
    )
    scheme_filter: Optional[str] = Field(
        None,
        description="Optional scheme name filter to restrict search",
        example="PM Kisan",
    )


class ChatResponse(BaseModel):
    """Assistant chat response with sources and performance metrics."""
    session_id: str
    question: str
    answer: str
    language: str
    sources: List[SourceCitation] = Field(default_factory=list)
    chunk_ids: List[str] = Field(default_factory=list)
    latency_ms: float = Field(..., description="Processing latency in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DeleteHistoryResponse(BaseModel):
    """Response returned upon deleting session history."""
    session_id: str
    deleted: bool
    message: str


class SchemesResponse(BaseModel):
    """List of indexed scheme names."""
    schemes: List[str]
    total_count: int


# ==============================================================================
# Chat History Models
# ==============================================================================

class ChatHistoryMessage(BaseModel):
    """Single chat history record."""
    role: Literal["user", "assistant"]
    content: str
    sources: Optional[List[Dict[str, Any]]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatSessionHistory(BaseModel):
    """Full session history schema."""
    session_id: str
    messages: List[ChatHistoryMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
