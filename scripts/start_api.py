#!/usr/bin/env python
"""Start the FastAPI server."""
import sys

sys.path.insert(0, "src")

import uvicorn

from jarvis.api.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5180)