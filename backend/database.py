import sys
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

# Ensure current directory is in sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from config import settings

# Async MongoDB client and database global instance
client: AsyncIOMotorClient = AsyncIOMotorClient(settings.MONGODB_URL)
db: AsyncIOMotorDatabase = client[settings.DB_NAME]


async def get_db() -> AsyncIOMotorDatabase:
    """FastAPI dependency that returns the database instance."""
    return db


def get_sync_db():
    """Synchronous helper using pymongo for non-async scripts if needed."""
    from pymongo import MongoClient

    sync_client = MongoClient(settings.MONGODB_URL)
    return sync_client[settings.DB_NAME]
