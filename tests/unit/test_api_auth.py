from fastapi.testclient import TestClient

from jarvis.api.main import app

client = TestClient(app)

def test_unauthenticated_access():
    """Test that endpoints return 401 for unauthenticated users."""
    endpoints = [
        ("GET", "/api/v1/stream"),
        ("POST", "/api/v1/cycles/run"),
        ("GET", "/api/v1/cycles"),
        ("GET", "/api/v1/signals"),
    ]
    for method, path in endpoints:
        if method == "GET":
            response = client.get(path)
        else:
            response = client.post(path, json={})
        assert response.status_code == 401, f"{method} {path} returned {response.status_code}"

def test_viewer_access_forbidden():
    """Test that VIEWER cannot access OWNER endpoints."""
    from jarvis.api.auth import UserInDB, get_current_user
    
    async def override_get_current_user():
        return UserInDB(id="1", username="viewer", password_hash="", role="VIEWER", active=True)
        
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    try:
        response = client.post("/api/v1/cycles/run", json={})
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
    finally:
        app.dependency_overrides.clear()
