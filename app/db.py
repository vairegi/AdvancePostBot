from motor.motor_asyncio import AsyncIOMotorClient
from app.config import MONGODB_URI, MONGODB_DB

client = AsyncIOMotorClient(MONGODB_URI)
db = client[MONGODB_DB]

users = db["users"]
channels = db["channels"]
drafts = db["drafts"]
saved_posts = db["saved_posts"]


async def init_indexes():
    await users.create_index("user_id", unique=True)
    await channels.create_index([("user_id", 1), ("chat_id", 1)], unique=True)
    await drafts.create_index("user_id", unique=True)


def empty_draft():
    return {
        "user_id": 0,
        "title": "Untitled Post",
        "text": "",
        "media_type": None,
        "media_file_id": None,
        "buttons": [],
        "buttons_per_row": 2,
        "table": None,
        "channel_id": None,
        "channel_title": None,
        "auto_delete_seconds": 0,
        "silent": False,
        "waiting_for": None,
    }