"""Verification test suite for SchemeSaathi REST API endpoints."""

import sys
import time
from pathlib import Path

# Add backend directory to path
backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("\n" + "=" * 70, flush=True)
print(" 🚀 SchemeSaathi REST API Endpoints Verification", flush=True)
print("=" * 70, flush=True)

# 1. Test /health
print("\n[1/6] Testing GET /health ...", flush=True)
res_health = client.get("/health")
assert res_health.status_code == 200
data_health = res_health.json()
assert data_health["app_name"] == "SchemeSaathi"
assert "indexed_documents_count" in data_health
print(f" ✓ Status: {res_health.status_code} | Indexed Docs: {data_health['indexed_documents_count']}", flush=True)

# 2. Test GET /schemes
print("\n[2/6] Testing GET /schemes ...", flush=True)
res_schemes = client.get("/schemes")
assert res_schemes.status_code == 200
data_schemes = res_schemes.json()
assert "schemes" in data_schemes
assert "total_count" in data_schemes
print(f" ✓ Status: {res_schemes.status_code} | Schemes found: {data_schemes['schemes']}", flush=True)

# 3. Test POST /chat request validation (Empty question -> 422)
print("\n[3/6] Testing POST /chat Request Validation ...", flush=True)
res_invalid = client.post("/chat", json={"session_id": "test_sess", "question": ""})
assert res_invalid.status_code == 422
print(" ✓ Validation error correctly rejected with 422 Unprocessable Entity", flush=True)

# 4. Test POST /chat with valid question
print("\n[4/6] Testing POST /chat with valid query ...", flush=True)
session_test_id = f"test_session_{int(time.time())}"
chat_payload = {
    "session_id": session_test_id,
    "question": "What is the financial assistance provided under PM Kisan?",
}
res_chat = client.post("/chat", json=chat_payload)
assert res_chat.status_code == 200
data_chat = res_chat.json()
assert data_chat["session_id"] == session_test_id
assert "answer" in data_chat
assert "sources" in data_chat
assert "chunk_ids" in data_chat
assert "latency_ms" in data_chat
print(f" ✓ Status: {res_chat.status_code}", flush=True)
print(f"   Language:   {data_chat['language']}", flush=True)
print(f"   Latency:    {data_chat['latency_ms']} ms", flush=True)
print(f"   Chunk IDs:  {data_chat['chunk_ids']}", flush=True)
print(f"   Answer:     {data_chat['answer'][:120]}...", flush=True)

# 5. Test GET /history/{session_id}
print(f"\n[5/6] Testing GET /history/{session_test_id} ...", flush=True)
res_hist = client.get(f"/history/{session_test_id}")
assert res_hist.status_code == 200
data_hist = res_hist.json()
assert len(data_hist["messages"]) >= 2  # user + assistant
print(f" ✓ Status: {res_hist.status_code} | Total recorded messages: {len(data_hist['messages'])}", flush=True)

# 6. Test DELETE /history/{session_id}
print(f"\n[6/6] Testing DELETE /history/{session_test_id} ...", flush=True)
res_del = client.delete(f"/history/{session_test_id}")
assert res_del.status_code == 200
data_del = res_del.json()
assert data_del["deleted"] is True
print(f" ✓ Status: {res_del.status_code} | {data_del['message']}", flush=True)

# Verify 404 after deletion
res_post_del = client.get(f"/history/{session_test_id}")
assert res_post_del.status_code == 404
print(" ✓ Subsequent GET /history returned 404 Not Found as expected", flush=True)

print("\n" + "=" * 70, flush=True)
print(" 🎉 ALL API ENDPOINTS VERIFIED & FUNCTIONING PERFECTLY! 🎉", flush=True)
print("=" * 70 + "\n", flush=True)

