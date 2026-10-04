import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.core.config import settings

logger = logging.getLogger("db.supabase_client")

class DatabaseClient:
    def __init__(self):
        self.supabase_url = settings.SUPABASE_URL
        self.supabase_key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY
        self.database_url = settings.DATABASE_URL
        self.supabase_client = None
        self.async_pool = None

        # Local in-memory / JSON store fallback for testing or when external DB is not connected
        self._local_universities: Dict[str, Dict[str, Any]] = {}
        self._local_majors: Dict[str, Dict[str, Any]] = {}
        self._local_scores: List[Dict[str, Any]] = []
        self._local_exam_scores: List[Dict[str, Any]] = []
        self._local_crawl_logs: List[Dict[str, Any]] = []

        self._init_clients()

    def _init_clients(self):
        if self.supabase_url and self.supabase_key:
            try:
                from supabase import create_client, Client
                self.supabase_client: Client = create_client(self.supabase_url, self.supabase_key)
                logger.info("Connected to Supabase client successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Supabase client: {e}. Using local store fallback.")

    async def get_pg_pool(self):
        """Initializes or returns asyncpg connection pool if DATABASE_URL is configured."""
        if not self.async_pool and self.database_url:
            try:
                import asyncpg
                self.async_pool = await asyncpg.create_pool(self.database_url, min_size=1, max_size=10)
                logger.info("Connected to PostgreSQL asyncpg pool successfully")
            except Exception as e:
                logger.warning(f"Failed to connect to asyncpg pool: {e}")
        return self.async_pool

    # --- Upsert Universities ---
    async def upsert_university(self, code: str, name: str, short_name: Optional[str] = None, region: Optional[str] = None, website: Optional[str] = None) -> Dict[str, Any]:
        data = {
            "code": code.upper().strip(),
            "name": name.strip(),
            "short_name": short_name.strip() if short_name else None,
            "region": region,
            "website": website,
            "updated_at": datetime.now().isoformat()
        }
        self._local_universities[data["code"]] = {**self._local_universities.get(data["code"], {}), **data}

        if self.supabase_client:
            try:
                res = self.supabase_client.table("universities").upsert(data, on_conflict="code").execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.error(f"Supabase upsert_university error: {e}")

        return self._local_universities[data["code"]]

    # --- Upsert Majors ---
    async def upsert_major(self, major_code: str, major_name: str, group_name: Optional[str] = None) -> Dict[str, Any]:
        key = f"{major_code.strip()}_{major_name.strip()}"
        data = {
            "major_code": major_code.strip(),
            "major_name": major_name.strip(),
            "group_name": group_name
        }
        self._local_majors[key] = data

        if self.supabase_client:
            try:
                res = self.supabase_client.table("majors").upsert(data, on_conflict="major_code,major_name").execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.error(f"Supabase upsert_major error: {e}")

        return data

    # --- Save Admission Scores ---
    async def save_admission_scores(self, scores: List[Dict[str, Any]]) -> int:
        if not scores:
            return 0

        saved_count = 0
        for item in scores:
            self._local_scores.append(item)
            saved_count += 1

        if self.supabase_client:
            try:
                # Batch upsert in chunks of 100
                chunk_size = 100
                for i in range(0, len(scores), chunk_size):
                    chunk = scores[i:i + chunk_size]
                    self.supabase_client.table("admission_scores").upsert(chunk, on_conflict="university_id,major_id,year").execute()
            except Exception as e:
                logger.error(f"Supabase save_admission_scores error: {e}")

        return saved_count

    # --- Save Exam Scores (Anonymized) ---
    async def save_exam_scores(self, exam_records: List[Dict[str, Any]]) -> int:
        if not exam_records:
            return 0

        for rec in exam_records:
            self._local_exam_scores.append(rec)

        if self.supabase_client:
            try:
                chunk_size = 200
                for i in range(0, len(exam_records), chunk_size):
                    chunk = exam_records[i:i + chunk_size]
                    self.supabase_client.table("exam_scores").insert(chunk).execute()
            except Exception as e:
                logger.error(f"Supabase save_exam_scores error: {e}")

        return len(exam_records)

    # --- Crawl Logs Tracking ---
    async def log_crawl_start(self, source_name: str, source_url: str) -> str:
        log_entry = {
            "id": f"log_{int(datetime.now().timestamp())}",
            "source_name": source_name,
            "source_url": source_url,
            "status": "running",
            "records_count": 0,
            "started_at": datetime.now().isoformat()
        }
        self._local_crawl_logs.append(log_entry)

        if self.supabase_client:
            try:
                res = self.supabase_client.table("crawl_logs").insert(log_entry).execute()
                if res.data:
                    return res.data[0].get("id")
            except Exception as e:
                logger.error(f"Supabase log_crawl_start error: {e}")

        return log_entry["id"]

    async def log_crawl_finish(self, log_id: str, status: str, records_count: int, error_message: Optional[str] = None):
        finished_at = datetime.now().isoformat()
        for log in self._local_crawl_logs:
            if log.get("id") == log_id:
                log["status"] = status
                log["records_count"] = records_count
                log["error_message"] = error_message
                log["finished_at"] = finished_at
                break

        if self.supabase_client:
            try:
                self.supabase_client.table("crawl_logs").update({
                    "status": status,
                    "records_count": records_count,
                    "error_message": error_message,
                    "finished_at": finished_at
                }).eq("id", log_id).execute()
            except Exception as e:
                logger.error(f"Supabase log_crawl_finish error: {e}")

    # --- Queries ---
    async def query_admission_scores(
        self,
        keyword: Optional[str] = None,
        university_code: Optional[str] = None,
        year: Optional[int] = None,
        subject_group: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        # If asyncpg pool is available, run high-speed SQL query
        pool = await self.get_pg_pool()
        if pool:
            try:
                async with pool.acquire() as conn:
                    query = """
                        SELECT u.code as uni_code, u.name as uni_name, u.region,
                               m.major_code, m.major_name, m.group_name,
                               a.year, a.subject_groups, a.cutoff_score, a.note, a.source
                        FROM admission_scores a
                        JOIN universities u ON u.id = a.university_id
                        JOIN majors m ON m.id = a.major_id
                        WHERE ($1::INT IS NULL OR a.year = $1)
                          AND ($2::TEXT IS NULL OR u.code = $2)
                          AND ($3::TEXT IS NULL OR $3 = ANY(a.subject_groups))
                          AND ($4::TEXT IS NULL OR m.major_name ILIKE '%' || $4 || '%' OR u.name ILIKE '%' || $4 || '%')
                        ORDER BY a.year DESC, a.cutoff_score DESC
                        LIMIT $5;
                    """
                    rows = await conn.fetch(query, year, university_code, subject_group, keyword, limit)
                    return [dict(r) for r in rows]
            except Exception as e:
                logger.warning(f"asyncpg query error: {e}. Falling back to Supabase/Memory query.")

        # Fallback to Supabase client query
        if self.supabase_client:
            try:
                q = self.supabase_client.table("admission_scores").select("*, universities(*), majors(*)")
                if year:
                    q = q.eq("year", year)
                if subject_group:
                    q = q.contains("subject_groups", [subject_group])
                q = q.limit(limit)
                res = q.execute()
                if res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"Supabase query error: {e}")

        # Local in-memory filter fallback
        filtered = self._local_scores
        if year:
            filtered = [s for s in filtered if s.get("year") == year]
        if subject_group:
            filtered = [s for s in filtered if subject_group in s.get("subject_groups", [])]
        if university_code:
            filtered = [s for s in filtered if s.get("uni_code") == university_code]
        if keyword:
            k = keyword.lower()
            filtered = [
                s for s in filtered
                if k in s.get("major_name", "").lower() or k in s.get("uni_name", "").lower()
            ]
        return filtered[:limit]

# Singleton instance
db_client = DatabaseClient()

async def get_db() -> DatabaseClient:
    """Dependency injection helper for FastAPI endpoints."""
    return db_client
