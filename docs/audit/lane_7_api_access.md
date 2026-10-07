# Lane 7: API and Access Control Audit

## Summary
- **PASS**: 4
- **FAIL**: 4
- **UNVERIFIED**: 2
- **BLOCKERS**: No immediate blockers for continuing development, but security/auth controls are missing and rate limiter order is flawed.

## Test Results

### 1. Server Binds to 127.0.0.1 by Default (PASS)
**Finding:** `scripts/start_api.py` hardcodes the Uvicorn host to `127.0.0.1`.
**Evidence:** Code inspection of `c:/jarvis/scripts/start_api.py` line 10.

### 2. Unauthenticated Gets 401 (PASS)
**Finding:** Unauthenticated requests to protected endpoints (e.g., `/api/v1/signals`) correctly return `401 Unauthorized`.
**Evidence:** 
```json
{"detail":"Not authenticated"}
```

### 3. Cookies HttpOnly/SameSite (PASS)
**Finding:** Access and refresh tokens are set as cookies with `HttpOnly` and `SameSite=strict`.
**Evidence:** 
```
Set-Cookie: access_token=...; HttpOnly; Max-Age=900; Path=/; SameSite=strict
```

### 4. CORS Allowlist (PASS)
**Finding:** `main.py` configures `CORSMiddleware` with a specific allowlist (`localhost:5173`, `127.0.0.1:5173`, etc.). Requests from `Origin: http://evil.com` do not receive `Access-Control-Allow-Origin`.

### 5. Rate Limits (PASS)
**Finding:** The custom rate limiting middleware correctly caps `/cycles/run` to 1 per minute and reads to 60 per minute.
**Evidence:** Calling `/cycles/run` twice rapidly returns `429 Too Many Requests`.

### 6. Role-Based Access Control (VIEWER limitations) (FAIL)
**Finding:** 
- `POST /cycles/run` returned `429 Rate Limited` instead of `403 Forbidden` because the rate-limiting middleware evaluates the request *before* authentication/authorization middleware. This leaks information and allows unauthenticated users to consume the rate limit quota.
- `PATCH /config/instruments/{symbol}` returns `404 Not Found` (endpoint not implemented), so RBAC on it could not be fully tested.

### 7. Lockout After 5 Failed Logins (FAIL)
**Finding:** There is no account lockout logic implemented in `src/jarvis/api/routes/auth.py`. Failed logins only create an audit log and return `401 Invalid credentials` indefinitely.

### 8. Error Envelope with request_id (FAIL)
**Finding:** Handled exceptions return the correct envelope, but FastAPI/Pydantic validation errors (e.g. invalid query parameters like `?limit=abc`) bypass the custom exception handler and return the default FastAPI 422 array format, lacking the `error.code`, `error.message`, and `error.request_id` envelope.
**Evidence:**
```json
{"detail":[{"type":"int_parsing","loc":["query","limit"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":"abc"}]}
```

### 9. No Stack Traces (PASS)
**Finding:** 500 errors and validation errors do not leak Python stack traces to the client.

### 10. SSE Named Events & Reconnect (UNVERIFIED)
**Finding:** The `/api/v1/stream` endpoint exists and accepts connections, but the emission of specific named events (`signal.created`, `signal.updated`, `cycle.status`, `agent.health`) could not be fully simulated without triggering a full pipeline run, which was blocked by the missing/unhealthy database adapter.
