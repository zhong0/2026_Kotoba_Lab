import uvicorn

from app.core.config import app_config as config

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=config.SERVER_PORT, reload=config.DEBUG)
