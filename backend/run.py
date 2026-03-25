"""Entry point for running the Zaisaku FastAPI server locally."""

import uvicorn

from zaisaku.api.app import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("run:app", host="127.0.0.0", port=8000, reload=True)
