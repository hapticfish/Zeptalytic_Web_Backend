"""Compatibility entrypoint for local runs.

Keeps a simple root-level module while the real application lives in app.main.
"""

from app.main import app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
