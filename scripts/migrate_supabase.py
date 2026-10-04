import asyncio
import os
import sys
import asyncpg

async def run_migration(db_password: str):
    project_ref = "ijkilhwpwxdkoxhgnjut"
    conn_str = f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"
    schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "schema.sql")

    print(f"Connecting to Supabase PostgreSQL at db.{project_ref}.supabase.co:5432...")
    try:
        conn = await asyncpg.connect(conn_str)
        print("Connected successfully!")
    except Exception as e:
        print(f"Connection with port 5432 failed: {e}. Trying Supavisor pooler at port 6543...")
        conn_str = f"postgresql://postgres.{project_ref}:{db_password}@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres"
        conn = await asyncpg.connect(conn_str)
        print("Connected via pooler successfully!")

    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()

    print("Executing schema.sql...")
    await conn.execute(sql)
    print("Schema migration completed successfully!")

    # Verify tables
    tables = await conn.fetch("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    print("Created tables in public schema:")
    for t in tables:
        print(f" - {t['table_name']}")

    await conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pwd = sys.argv[1]
    else:
        pwd = os.getenv("DATABASE_PASSWORD", "")
    if not pwd:
        print("Usage: python migrate_supabase.py <database_password>")
        sys.exit(1)
    asyncio.run(run_migration(pwd))
