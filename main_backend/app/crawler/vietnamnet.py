import re
import logging
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from app.crawler.base import BaseCrawler
from app.db.supabase_client import db_client

logger = logging.getLogger("crawler.vietnamnet")

SUBJECT_KEY_MAP = {
    "toán": "math",
    "ngữ văn": "literature",
    "văn": "literature",
    "lí": "physics",
    "vật lí": "physics",
    "hóa": "chemistry",
    "hóa học": "chemistry",
    "sinh": "biology",
    "sinh học": "biology",
    "lịch sử": "history",
    "sử": "history",
    "địa": "geography",
    "địa lí": "geography",
    "tiếng anh": "foreign_language",
    "ngoại ngữ": "foreign_language",
    "gdcd": "civic_education",
    "giáo dục công dân": "civic_education"
}

class VietnamNetExamCrawler(BaseCrawler):
    """
    Crawler for VietnamNet High School Graduation Exam Scores
    - URL Pattern: https://vietnamnet.vn/giao-duc/diem-thi/tra-cuu-diem-thi-tot-nghiep-thpt/{year}/{idx}.html
    - Decree 13/2023 Compliance: Only extracts examination scores & anonymous index (No PII).
    - Batch insertion to exam_scores table with checkpoint resumption.
    """
    def __init__(self, year: int = 2024):
        super().__init__(
            source_name=f"vietnamnet_exam_{year}",
            base_url="https://vietnamnet.vn"
        )
        self.year = year
        self.url_template = f"{self.base_url}/giao-duc/diem-thi/tra-cuu-diem-thi-tot-nghiep-thpt/{year}/{{sbd}}.html"

    def parse(self, html: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Parses candidate exam score table into structured dictionary.
        Example: {'math': 8.4, 'literature': 6.75, 'physics': 6.0, ...}
        """
        soup = BeautifulSoup(html, "html.parser")
        sbd = kwargs.get("sbd", "")

        table = soup.find("table")
        if not table:
            return None

        scores: Dict[str, Any] = {
            "exam_number": sbd,
            "year": self.year,
            "province_code": sbd[:2] if len(sbd) >= 2 else "01",
            "math": None,
            "literature": None,
            "physics": None,
            "chemistry": None,
            "biology": None,
            "history": None,
            "geography": None,
            "foreign_language": None,
            "civic_education": None,
            "total_score": 0.0
        }

        # Support both formats:
        # Format A: 2-column key-value rows (e.g. <tr><td>Toán</td><td>8.40</td></tr>)
        # Format B: Multi-column header/data rows (e.g. <tr><th>Toán</th><th>Văn</th></tr><tr><td>8.4</td><td>7.5</td></tr>)
        rows = table.find_all("tr")
        matched_any = False

        # First check Format A (2 cells per row: [Subject, Score])
        for r in rows:
            cells = r.find_all(["th", "td"])
            if len(cells) == 2:
                h = cells[0].get_text(strip=True).lower()
                v = cells[1].get_text(strip=True).replace(",", ".")
                for subj_key, field_name in SUBJECT_KEY_MAP.items():
                    if subj_key == h or subj_key in h:
                        try:
                            scores[field_name] = float(v)
                            matched_any = True
                        except (ValueError, TypeError):
                            pass
                        break

        # If Format A didn't match and we have at least 2 rows with > 2 cells, try Format B
        if not matched_any and len(rows) >= 2:
            headers = [c.get_text(strip=True).lower() for c in rows[0].find_all(["th", "td"])]
            values = [c.get_text(strip=True).replace(",", ".") for c in rows[1].find_all(["th", "td"])]

            for h, v in zip(headers, values):
                for subj_key, field_name in SUBJECT_KEY_MAP.items():
                    if subj_key in h:
                        try:
                            score_val = float(v)
                            scores[field_name] = score_val
                        except (ValueError, TypeError):
                            pass
                        break

        # Calculate total available score
        valid_scores = [v for k, v in scores.items() if isinstance(v, (int, float)) and k not in ["year", "total_score"]]
        scores["total_score"] = round(sum(valid_scores), 2) if valid_scores else 0.0

        return scores if valid_scores else None

    async def save(self, records: List[Dict[str, Any]]) -> int:
        return await db_client.save_exam_scores(records)

    async def run(self, start_idx: int = 1, end_idx: int = 100, province_code: str = "01") -> Dict[str, Any]:
        """
        Runs batch crawling for student IDs in a specified range.
        Format of SBD in Vietnam: 8 digits (e.g., 01000001 to 01000100 for Hanoi).
        """
        log_id = await db_client.log_crawl_start(
            source_name=self.source_name,
            source_url=self.url_template.format(sbd=f"{province_code}{start_idx:06d}")
        )

        checkpoint = self.load_checkpoint()
        last_idx = checkpoint.get("last_idx", start_idx - 1)
        current_start = max(start_idx, last_idx + 1)

        batch_records = []
        total_saved = checkpoint.get("total_saved", 0)

        try:
            logger.info(f"Starting VietnamNet crawl for year {self.year}, SBD range {province_code}{current_start:06d} -> {province_code}{end_idx:06d}")

            for i in range(current_start, end_idx + 1):
                sbd = f"{province_code}{i:06d}"
                url = self.url_template.format(sbd=sbd)

                html = await self.fetch(url)
                if html:
                    record = self.parse(html, sbd=sbd)
                    if record:
                        batch_records.append(record)

                # Batch save every 25 records
                if len(batch_records) >= 25 or i == end_idx:
                    if batch_records:
                        saved = await self.save(batch_records)
                        total_saved += saved
                        logger.info(f"Saved batch of {saved} exam records (Current SBD: {sbd})")
                        batch_records = []

                    self.save_checkpoint({
                        "last_idx": i,
                        "total_saved": total_saved,
                        "province_code": province_code
                    })

            await db_client.log_crawl_finish(
                log_id=log_id,
                status="success",
                records_count=total_saved
            )
            return {
                "status": "success",
                "total_records": total_saved,
                "year": self.year
            }
        except Exception as e:
            logger.error(f"VietnamNet crawl error: {e}", exc_info=True)
            await db_client.log_crawl_finish(
                log_id=log_id,
                status="failed",
                records_count=total_saved,
                error_message=str(e)
            )
            return {"status": "failed", "error": str(e)}
        finally:
            await self.close()
