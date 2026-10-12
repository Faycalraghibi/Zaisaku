"""Entry point for running the Zaisaku FastAPI server locally."""

import uvicorn

from zaisaku.api.app import create_app
from zaisaku.config import get_settings

app = create_app()

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run("run:app", host=settings.app_host, port=settings.app_port, reload=True)
