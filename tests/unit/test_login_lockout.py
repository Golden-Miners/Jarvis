from fastapi.testclient import TestClient

from jarvis.api.main import app

client = TestClient(app)

def test_login_lockout():
    """Test that login is locked out after 5 failed attempts."""
    username = "wronguser"
    password = "wrongpassword"
    
    # 5 failed attempts should return 401
    for _ in range(5):
        response = client.post(
            "/api/v1/auth/login", json={"username": username, "password": password}
        )
        assert response.status_code == 401
        
    # The 6th attempt should be blocked by rate limit 429
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 429
    assert "Too many failed login attempts" in response.text
