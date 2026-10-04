import asyncio
import os
import sys
import json

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.db.supabase_client import DatabaseClient

async def seed_data():
    db = DatabaseClient()
    if not db.supabase_client:
        print("ERROR: Supabase client not initialized. Check SUPABASE_URL and SUPABASE_KEY.")
        return

    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "data")
    unis_path = os.path.join(data_dir, "universities_database.json")
    majors_path = os.path.join(data_dir, "majors_database.json")

    print(f"Connecting to Supabase at: {settings.SUPABASE_URL}")

    # 1. Seed Universities
    if os.path.exists(unis_path):
        with open(unis_path, "r", encoding="utf-8") as f:
            unis = json.load(f)
        print(f"Seeding {len(unis)} universities...")
        for u in unis:
            await db.upsert_university(
                code=u.get("code", ""),
                name=u.get("name", ""),
                short_name=u.get("short_name"),
                region=u.get("region"),
                website=u.get("website")
            )
        print("Universities seeded successfully!")

    # 2. Seed Majors
    if os.path.exists(majors_path):
        with open(majors_path, "r", encoding="utf-8") as f:
            majors = json.load(f)
        print(f"Seeding {len(majors)} majors...")
        for m in majors:
            await db.upsert_major(
                major_code=m.get("major_code", ""),
                major_name=m.get("major_name", ""),
                group_name=m.get("group_name")
            )
        print("Majors seeded successfully!")

    print("Database seeding completed!")

if __name__ == "__main__":
    asyncio.run(seed_data())
