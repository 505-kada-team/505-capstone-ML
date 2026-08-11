from typing import Optional

from pymongo import MongoClient

from app.core.config import settings


_client: Optional[MongoClient] = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)
    return _client


def get_db():
    return get_client()[settings.mongodb_db]


def close_mongo() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
