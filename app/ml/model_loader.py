from pathlib import Path
from threading import Lock
from typing import Optional

import joblib

from app.core.config import resolve_project_path, settings


class ModelLoader:
    _instance: Optional["ModelLoader"] = None
    _lock = Lock()

    def __new__(cls) -> "ModelLoader":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._model = None
        return cls._instance

    def load(self):
        if self._model is None:
            model_path = resolve_project_path(settings.model_path)
            if not model_path.exists():
                raise FileNotFoundError(f"Model file not found at {model_path}")
            self._model = joblib.load(model_path)
        return self._model


model_loader = ModelLoader()


def get_model():
    return model_loader.load()
