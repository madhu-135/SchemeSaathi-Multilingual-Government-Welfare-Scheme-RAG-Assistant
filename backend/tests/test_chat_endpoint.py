"""Pytest unit tests for the /chat and history endpoints with a mocked MongoDB."""

from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

# Pre-load embeddings and torch runtime on Windows for OpenMP stability
import app.embeddings  # noqa: F401
import faiss  # noqa: F401
from app.main import app
from app.models import ChatHistoryMessage, ChatSessionHistory


@pytest.fixture
def client():
    """Create a FastAPI test client with mocked MongoDB startup/shutdown."""
    with patch("app.main.connect_to_mongo", new_callable=AsyncMock), \
         patch("app.main.close_mongo_connection", new_callable=AsyncMock):
        with TestClient(app) as test_client:
            yield test_client


def test_post_chat_endpoint_success(client):
    """Verify POST /chat responds with grounded RAG answer and stores message in mocked MongoDB."""
    mock_save = AsyncMock(return_value=True)
    mock_history = AsyncMock(return_value=None)

    with patch("app.main.save_chat_message", mock_save), \
         patch("app.main.get_session_history", mock_history):

        payload = {
            "session_id": "test_pytest_session_01",
            "question": "What is the financial support provided under PM-KISAN?",
        }
        response = client.post("/chat", json=payload)

        assert response.status_code == 200
        data = response.json()

        # Validate response schema
        assert data["session_id"] == "test_pytest_session_01"
        assert data["question"] == payload["question"]
        assert isinstance(data["answer"], str)
        assert len(data["answer"]) > 0
        assert data["language"] == "en"
        assert isinstance(data["sources"], list)
        assert isinstance(data["chunk_ids"], list)
        assert "latency_ms" in data
        assert data["latency_ms"] >= 0

        # Verify that save_chat_message was called on mocked Mongo
        mock_save.assert_called_once()
        call_kwargs = mock_save.call_args.kwargs
        assert call_kwargs["session_id"] == "test_pytest_session_01"
        assert call_kwargs["user_query"] == payload["question"]
        assert len(call_kwargs["assistant_response"]) > 0


def test_post_chat_request_validation(client):
    """Verify POST /chat rejects invalid or missing payload fields with HTTP 422."""
    # Missing 'question' field
    res_missing_q = client.post("/chat", json={"session_id": "sess_1"})
    assert res_missing_q.status_code == 422

    # Missing 'session_id' field
    res_missing_sess = client.post("/chat", json={"question": "Tell me about schemes"})
    assert res_missing_sess.status_code == 422

    # Empty JSON body
    res_empty = client.post("/chat", json={})
    assert res_empty.status_code == 422


def test_post_chat_irrelevant_query_not_found(client):
    """Verify POST /chat returns 'not found' fallback for out-of-scope query."""
    mock_save = AsyncMock(return_value=True)
    mock_history = AsyncMock(return_value=None)

    with patch("app.main.save_chat_message", mock_save), \
         patch("app.main.get_session_history", mock_history):

        payload = {
            "session_id": "test_oos_session",
            "question": "How do I bake chocolate chip cookies in an oven?",
        }
        response = client.post("/chat", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert "couldn't find" in data["answer"].lower()
        assert data["sources"] == []
        assert data["chunk_ids"] == []


def test_history_endpoints_with_mocked_mongo(client):
    """Verify GET and DELETE /history/{session_id} using mocked MongoDB persistence."""
    fake_session = ChatSessionHistory(
        session_id="mock_session_123",
        messages=[
            ChatHistoryMessage(role="user", content="What is PM Kisan?"),
            ChatHistoryMessage(role="assistant", content="PM Kisan is an income support scheme."),
        ],
    )

    # 1. Test GET /history/{session_id} when session exists
    with patch("app.main.get_session_history", AsyncMock(return_value=fake_session)):
        res_get = client.get("/history/mock_session_123")
        assert res_get.status_code == 200
        data = res_get.json()
        assert data["session_id"] == "mock_session_123"
        assert len(data["messages"]) == 2

    # 2. Test GET /history/{session_id} when session does not exist (404)
    with patch("app.main.get_session_history", AsyncMock(return_value=None)):
        res_not_found = client.get("/history/nonexistent_session")
        assert res_not_found.status_code == 404

    # 3. Test DELETE /history/{session_id}
    with patch("app.main.delete_session_history", AsyncMock(return_value=True)):
        res_del = client.delete("/history/mock_session_123")
        assert res_del.status_code == 200
        del_data = res_del.json()
        assert del_data["deleted"] is True
        assert del_data["session_id"] == "mock_session_123"

