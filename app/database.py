from motor.motor_asyncio import AsyncIOMotorClient
import os
from typing import Optional

class Database:
    client: Optional[AsyncIOMotorClient] = None
    db = None

    @classmethod
    async def connect_db(cls):
        try:
            MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
            cls.client = AsyncIOMotorClient(MONGO_URL)
            cls.db = cls.client["ems"]
            # Verify connection
            await cls.client.admin.command('ping')
            print("Successfully connected to MongoDB")
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            raise

    @classmethod
    async def close_db(cls):
        if cls.client:
            await cls.client.close()
            print("MongoDB connection closed")

    @classmethod
    def get_db(cls):
        return cls.db