import re
import time
import logging
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from app.crawler.base import BaseCrawler
from app.db.supabase_client import db_client

logger = logging.getLogger("crawler.tuyensinh247")

class TuyenSinh247Crawler(BaseCrawler):
    """
    Crawler for Tuyensinh247 (diemthi.tuyensinh247.com)
    - Extracts university directory
    - Extracts admission benchmarks by major, exam combination, and year
    - 100% BeautifulSoup + CSS selector parsing (Zero Gemini API tokens spent)
    """
    def __init__(self):
        super().__init__(
            source_name="tuyensinh247",
            base_url="https://diemthi.tuyensinh247.com"
        )
        self.directory_url = f"{self.base_url}/diem-chuan.html"

    async def get_university_links(self) -> List[Dict[str, str]]:
        """Scrapes list of all universities and their benchmark URLs."""
        html = await self.fetch(self.directory_url)
        if not html:
            logger.error("Failed to fetch Tuyensinh247 university directory")
            return []

        soup = BeautifulSoup(html, "html.parser")
        links = soup.find_all("a", href=True)
        unis = []
        seen = set()

        for a in links:
            href = a["href"]
            text = a.get_text(strip=True)
            if "/diem-chuan/" in href and href.endswith(".html") and text:
                full_url = href if href.startswith("http") else f"{self.base_url}{href}"
                if full_url in seen or full_url == self.directory_url:
                    continue

                # Extract code and name from format: "BKA-Đại Học Bách Khoa Hà Nội"
                match = re.match(r"^([A-Z0-9]{2,6})\s*-\s*(.+)$", text)
                if match:
                    code, name = match.group(1).strip(), match.group(2).strip()
                else:
                    # Alternative: extract from URL suffix e.g. dai-hoc-bach-khoa-ha-noi-BKA.html
                    code_match = re.search(r"-([A-Z0-9]{2,6})\.html", href)
                    code = code_match.group(1) if code_match else "UNI"
                    name = text

                unis.append({
                    "code": code,
                    "name": name,
                    "url": full_url
                })
                seen.add(full_url)

        logger.info(f"Discovered {len(unis)} universities on Tuyensinh247")
        return unis

    def parse(self, html: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Parses university benchmark detail page into structured admission scores.
        Extracts year, major code, major name, subject groups, cutoff score, and notes.
        """
        soup = BeautifulSoup(html, "html.parser")
        uni_code = kwargs.get("uni_code", "UNKNOWN")
        uni_name = kwargs.get("uni_name", "UNKNOWN")

        records: List[Dict[str, Any]] = []

        # Find year headings e.g. "Điểm chuẩn theo phương thức Điểm thi THPT năm 2026"
        headings = soup.find_all(["h2", "h3", "h4", "div", "strong"])
        
        tables = soup.find_all("table")
        if not tables:
            return records

        for table in tables:
            # Detect year from previous sibling or parent header
            year = 2025 # Default fallback year
            prev = table.find_previous(["h2", "h3", "h4", "strong", "span"])
            if prev:
                prev_text = prev.get_text(strip=True)
                year_match = re.search(r"năm\s*(202[0-9])", prev_text, re.IGNORECASE)
                if year_match:
                    year = int(year_match.group(1))

            rows = table.find_all("tr")
            for r in rows:
                cols = r.find_all(["td", "th"])
                if len(cols) < 3:
                    continue

                col_texts = [c.get_text(strip=True) for c in cols]
                col0 = col_texts[0]

                # Skip header row
                if "tên ngành" in col0.lower() or "mã ngành" in col0.lower() or "tra cứu tại" in col0.lower():
                    continue

                # Structure format: [Tên ngành/mã ngành, Tổ hợp môn, Điểm chuẩn, (Ghi chú)]
                major_raw = col_texts[0]
                subj_raw = col_texts[1] if len(col_texts) > 1 else ""
                score_raw = col_texts[2] if len(col_texts) > 2 else ""
                note = col_texts[3] if len(col_texts) > 3 else ""

                # Extract score float
                score_match = re.search(r"([0-9]{1,2}(?:\.[0-9]{1,2})?)", score_raw)
                if not score_match:
                    continue
                cutoff_score = float(score_match.group(1))

                # Normalize subject groups: e.g. "A00; B00; D07" or "A00, A01"
                subject_groups = [
                    re.sub(r"[^A-Z0-9]", "", g).strip()
                    for g in re.split(r"[;,\/\s]+", subj_raw)
                    if re.match(r"^[A-Z][0-9]{2}$", re.sub(r"[^A-Z0-9]", "", g).strip())
                ]

                # Separate major code and major name if present e.g. "7480201 - Khoa học máy tính"
                m_code_match = re.search(r"^(7[0-9]{6}|[A-Z0-9]{2,8})\s*[-:]?\s*(.+)$", major_raw)
                if m_code_match:
                    major_code = m_code_match.group(1).strip()
                    major_name = m_code_match.group(2).strip()
                else:
                    major_code = f"M_{abs(hash(major_raw)) % 1000000}"
                    major_name = major_raw

                records.append({
                    "uni_code": uni_code,
                    "uni_name": uni_name,
                    "major_code": major_code,
                    "major_name": major_name,
                    "year": year,
                    "subject_groups": subject_groups if subject_groups else ["A00"],
                    "cutoff_score": cutoff_score,
                    "note": note,
                    "source": "tuyensinh247"
                })

        return records

    async def save(self, records: List[Dict[str, Any]]) -> int:
        """Stores universities, majors, and scores to DB."""
        if not records:
            return 0

        # 1. Upsert university
        uni_code = records[0]["uni_code"]
        uni_name = records[0]["uni_name"]
        await db_client.upsert_university(code=uni_code, name=uni_name, region="Toàn quốc")

        # 2. Upsert majors and admission scores
        for r in records:
            await db_client.upsert_major(major_code=r["major_code"], major_name=r["major_name"])

        return await db_client.save_admission_scores(records)

    async def run(self, max_universities: Optional[int] = None) -> Dict[str, Any]:
        """
        Executes weekly crawl cycle with checkpointing.
        """
        log_id = await db_client.log_crawl_start(
            source_name=self.source_name,
            source_url=self.directory_url
        )

        checkpoint = self.load_checkpoint()
        processed_codes = set(checkpoint.get("processed_codes", []))
        total_records = checkpoint.get("total_records", 0)

        try:
            unis = await self.get_university_links()
            if max_universities:
                unis = unis[:max_universities]

            for idx, uni in enumerate(unis, 1):
                if uni["code"] in processed_codes:
                    logger.debug(f"Skipping already crawled university: {uni['code']}")
                    continue

                logger.info(f"[{idx}/{len(unis)}] Crawling Tuyensinh247: {uni['code']} - {uni['name']}...")
                html = await self.fetch(uni["url"])
                if html:
                    records = self.parse(html, uni_code=uni["code"], uni_name=uni["name"])
                    if records:
                        saved = await self.save(records)
                        total_records += saved
                        logger.info(f"Saved {saved} scores for {uni['code']}")

                processed_codes.add(uni["code"])
                self.save_checkpoint({
                    "processed_codes": list(processed_codes),
                    "total_records": total_records,
                    "last_updated": time.time()
                })

            await db_client.log_crawl_finish(
                log_id=log_id,
                status="success",
                records_count=total_records
            )
            return {
                "status": "success",
                "universities_processed": len(processed_codes),
                "total_records": total_records
            }
        except Exception as e:
            logger.error(f"Tuyensinh247 crawl cycle failed: {e}", exc_info=True)
            await db_client.log_crawl_finish(
                log_id=log_id,
                status="failed",
                records_count=total_records,
                error_message=str(e)
            )
            return {"status": "failed", "error": str(e)}
        finally:
            await self.close()
