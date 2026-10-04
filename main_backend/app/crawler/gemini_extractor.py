import os
import json
import hashlib
import logging
import asyncio
from typing import Dict, Any, List, Optional
import httpx
from bs4 import BeautifulSoup
import markdownify
from pydantic import BaseModel, Field
from app.core.config import settings

logger = logging.getLogger("crawler.gemini_extractor")

class MajorScoreItem(BaseModel):
    major_code: str = Field(..., description="Mã ngành tuyển sinh (ví dụ: 7480201)")
    major_name: str = Field(..., description="Tên ngành đào tạo")
    subject_groups: List[str] = Field(default_factory=list, description="Tổ hợp môn xét tuyển: A00, D01, B00...")
    cutoff_score: float = Field(..., description="Điểm chuẩn trúng tuyển theo thang 30")
    quota: Optional[int] = Field(None, description="Chỉ tiêu tuyển sinh nếu có")
    note: Optional[str] = Field("", description="Ghi chú tiêu chí phụ hoặc học phí")

class UniversityAdmissionScheme(BaseModel):
    university_code: str = Field(..., description="Mã trường viết tắt: BKA, KHA, QHI...")
    university_name: str = Field(..., description="Tên trường đại học")
    year: int = Field(..., description="Năm tuyển sinh (ví dụ: 2025 hoặc 2026)")
    majors: List[MajorScoreItem] = Field(default_factory=list, description="Danh sách các ngành và điểm chuẩn")

class GeminiUnstructuredExtractor:
    """
    Optimized Gemini Extractor for Unstructured School Websites (HTML -> Markdown -> Gemini)
    - 75% Token reduction via BeautifulSoup cleanup & markdownify
    - Persistent SHA-256 Cache: Zero duplicate API calls
    - Structured Output with Pydantic JSON Schema
    - Exponential backoff retry handling
    """
    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY
        self.model = "gemini-2.5-flash"
        self.cache_dir = os.path.join(settings.CHECKPOINT_DIR, "gemini_cache")
        os.makedirs(self.cache_dir, exist_ok=True)

    def clean_html_to_markdown(self, raw_html: str) -> str:
        """
        Strips scripts, styles, navigations, footers, and converts to compact Markdown.
        Reduces token usage by up to 80%.
        """
        soup = BeautifulSoup(raw_html, "html.parser")

        # Strip useless tags
        for element in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "form", "iframe"]):
            element.decompose()

        cleaned_html = str(soup)
        md_text = markdownify.markdownify(cleaned_html, heading_style="ATX", strip=['img', 'a'])

        # Collapse excess empty lines
        lines = [line.strip() for line in md_text.splitlines() if line.strip()]
        compact_md = "\n".join(lines)

        # Truncate to maximum 12,000 characters to prevent token explosion
        return compact_md[:12000]

    def _get_cache_path(self, content_hash: str) -> str:
        return os.path.join(self.cache_dir, f"{content_hash}.json")

    def _get_cached_result(self, content_hash: str) -> Optional[Dict[str, Any]]:
        path = self._get_cache_path(content_hash)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    logger.info(f"Gemini Cache HIT for hash {content_hash[:8]}")
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error reading cache {path}: {e}")
        return None

    def _save_cache(self, content_hash: str, data: Dict[str, Any]):
        path = self._get_cache_path(content_hash)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Error writing cache {path}: {e}")

    async def extract_admission_data(self, raw_html: str, url: str = "") -> Optional[UniversityAdmissionScheme]:
        """
        Extracts structured admission scheme and scores from unstructured school HTML.
        Checks cache first -> if not cached, cleans to markdown -> calls Gemini with schema.
        """
        # 1. Check SHA-256 Hash Cache
        content_hash = hashlib.sha256(raw_html.encode("utf-8")).hexdigest()
        cached = self._get_cached_result(content_hash)
        if cached:
            try:
                return UniversityAdmissionScheme(**cached)
            except Exception:
                pass

        if not self.api_key:
            logger.error("GOOGLE_API_KEY is not configured for Gemini Extractor")
            return None

        # 2. Clean HTML to Markdown (Token Saving)
        markdown_content = self.clean_html_to_markdown(raw_html)
        if not markdown_content or len(markdown_content) < 50:
            logger.warning("HTML content too short or empty after cleaning.")
            return None

        prompt = (
            "Bạn là chuyên gia trích xuất dữ liệu tuyển sinh đại học Việt Nam. "
            "Hãy trích xuất thông tin điểm chuẩn, mã ngành, tên ngành, tổ hợp môn từ văn bản Markdown sau đây. "
            "Chỉ trích xuất số liệu chính xác được công bố trong văn bản, không tự bịa đặt. "
            "Trả về định dạng JSON thuần túy khớp với schema:\n\n"
            f"VĂN BẢN TRÍCH XUẤT:\n{markdown_content}"
        )

        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        schema = {
            "type": "object",
            "properties": {
                "university_code": {"type": "string", "description": "Mã trường viết tắt"},
                "university_name": {"type": "string", "description": "Tên trường đại học"},
                "year": {"type": "integer", "description": "Năm tuyển sinh"},
                "majors": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "major_code": {"type": "string", "description": "Mã ngành"},
                            "major_name": {"type": "string", "description": "Tên ngành"},
                            "subject_groups": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Tổ hợp xét tuyển"
                            },
                            "cutoff_score": {"type": "number", "description": "Điểm chuẩn"},
                            "quota": {"type": "integer", "description": "Chỉ tiêu tuyển sinh nếu có"},
                            "note": {"type": "string", "description": "Ghi chú"}
                        },
                        "required": ["major_code", "major_name", "cutoff_score"]
                    }
                }
            },
            "required": ["university_code", "university_name", "year", "majors"]
        }

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "response_mime_type": "application/json",
                "response_schema": schema,
                "temperature": 0.1
            }
        }

        # 3. Call Gemini API with Exponential Backoff
        for attempt in range(1, 4):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(api_url, json=payload)
                    if resp.status_code == 200:
                        res_json = resp.json()
                        text_output = res_json["candidates"][0]["content"]["parts"][0]["text"]
                        parsed_data = json.loads(text_output)

                        # Save to Cache
                        self._save_cache(content_hash, parsed_data)

                        result = UniversityAdmissionScheme(**parsed_data)
                        logger.info(f"Gemini Extracted {len(result.majors)} majors for {result.university_code} from {url}")
                        return result
                    elif resp.status_code == 429:
                        sleep_s = (2 ** attempt) * 2
                        logger.warning(f"Gemini Rate Limit (429). Retrying in {sleep_s}s...")
                        await asyncio.sleep(sleep_s)
                    else:
                        logger.error(f"Gemini API error {resp.status_code}: {resp.text[:300]}")
                        break
            except Exception as e:
                logger.error(f"Gemini extraction exception (Attempt {attempt}): {e}")
                await asyncio.sleep(2)

        return None

gemini_extractor = GeminiUnstructuredExtractor()
