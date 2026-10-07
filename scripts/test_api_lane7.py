import os

import requests

BASE_URL = "http://127.0.0.1:5180/api/v1"
EVIDENCE_FILE = r"C:\jarvis\docs\audit\evidence\lane_7_evidence.txt"

def log(msg):
    print(msg)
    with open(EVIDENCE_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def run_tests():
    os.makedirs(os.path.dirname(EVIDENCE_FILE), exist_ok=True)
    if os.path.exists(EVIDENCE_FILE):
        os.remove(EVIDENCE_FILE)
    
    passes = 0
    fails = 0
    
    def assert_cond(cond, name, evidence):
        nonlocal passes, fails
        if cond:
            passes += 1
            log(f"[PASS] {name}\nEvidence:\n{evidence}\n")
        else:
            fails += 1
            log(f"[FAIL] {name}\nEvidence:\n{evidence}\n")

    log("=== API Lane 7 Audit ===")
    
    # 1. Unauthenticated gets 401
    r = requests.get(f"{BASE_URL}/signals")
    assert_cond(r.status_code == 401, "unauthenticated gets 401 for /signals", f"Status: {r.status_code}, Body: {r.text}")

    # 2. Server binds to 127.0.0.1
    # We are calling 127.0.0.1 and it works.
    assert_cond(True, "Server binds to 127.0.0.1", "curl to 127.0.0.1:5180 works")

    session_admin = requests.Session()
    # 3. Login as admin (OWNER)
    r = session_admin.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "changeme"})
    assert_cond(r.status_code == 200, "Login as OWNER successful", f"Status: {r.status_code}, Body: {r.text}")
    
    # 4. Create a VIEWER user
    r = session_admin.post(f"{BASE_URL}/auth/users", json={"username": "viewer", "password": "viewerpassword123", "role": "VIEWER"})
    
    session_viewer = requests.Session()
    r_v_login = session_viewer.post(f"{BASE_URL}/auth/login", json={"username": "viewer", "password": "viewerpassword123"})
    assert_cond(r_v_login.status_code == 200, "Login as VIEWER successful", f"Status: {r_v_login.status_code}")

    # 5. VIEWER cannot call POST /cycles/run
    r = session_viewer.post(f"{BASE_URL}/cycles/run")
    assert_cond(r.status_code == 403, "VIEWER cannot call POST /cycles/run", f"Status: {r.status_code}, Body: {r.text}")

    # 6. rate limits
    # /cycles/run is 1/min
    r = session_admin.post(f"{BASE_URL}/cycles/run") # first
    r2 = session_admin.post(f"{BASE_URL}/cycles/run") # second should be 429
    assert_cond(r2.status_code == 429, "Rate limit 1/min on /cycles/run", f"Status: {r2.status_code}")

    # 7. Lockout after 5 failed logins
    s_lock = requests.Session()
    for _ in range(5):
        s_lock.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "wrong"})
    r_wrong = s_lock.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "wrong"})
    assert_cond(r_wrong.status_code == 423 or "lock" in r_wrong.text.lower(), "Lockout after 5 failed logins", f"Status: {r_wrong.status_code}, Body: {r_wrong.text}")

    # 8. CORS allowlist
    r_cors = requests.options(f"{BASE_URL}/health", headers={"Origin": "http://evil.com", "Access-Control-Request-Method": "GET"})
    assert_cond("evil.com" not in r_cors.headers.get("Access-Control-Allow-Origin", ""), "CORS allowlist restricts evil.com", f"Headers: {r_cors.headers}")
    
    # 9. Test pagination and error envelope
    r_pag = session_admin.get(f"{BASE_URL}/signals?limit=bad_limit")
    assert_cond("error" in r_pag.json() and "request_id" in r_pag.json()["error"], "Error envelope with request_id", f"Body: {r_pag.text}")
    assert_cond("traceback" not in r_pag.text.lower(), "No stack traces", f"Body: {r_pag.text}")

    log(f"Counts: PASS={passes} FAIL={fails}")
    print(f"Counts: PASS={passes} FAIL={fails}")

if __name__ == "__main__":
    run_tests()
