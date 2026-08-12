from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.ml.model_loader import get_model

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        get_model()
    except Exception as exc:
        app.state.model_warning = str(exc)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(api_router)