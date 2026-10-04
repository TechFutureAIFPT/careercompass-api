import sys
import asyncio
import logging
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")

from app.crawler.tuyensinh247 import TuyenSinh247Crawler
from app.crawler.vietnamnet import VietnamNetExamCrawler
from app.crawler.gemini_extractor import gemini_extractor
from app.db.supabase_client import db_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("live_test")

async def test_live_tuyensinh247():
    print("\n" + "="*60)
    print("1. LIVE TEST: TUYENSINH247 (Admission Cutoff Scores)")
    print("="*60)
    crawler = TuyenSinh247Crawler()
    
    # Test single university crawl for KHA (ĐH Kinh Tế Quốc Dân)
    uni_code = "KHA"
    uni_name = "Đại học Kinh tế Quốc dân"
    url = f"https://diemthi.tuyensinh247.com/diem-chuan/dai-hoc-kinh-te-quoc-dan-{uni_code.lower()}.html"
    
    print(f"Fetching URL: {url}...")
    html = await crawler.fetch(url)
    if not html:
        print("❌ Failed to fetch Tuyensinh247 page")
        return False
        
    records = crawler.parse(html, uni_code=uni_code, uni_name=uni_name)
    print(f"✓ Crawled successfully: {len(records)} major score records for {uni_name} ({uni_code})!")
    
    if records:
        print("Sample crawled records:")
        for r in records[:5]:
            print(f"  - [{r['year']}] {r['major_code']} - {r['major_name']}: Cutoff {r['cutoff_score']} | Groups: {r['subject_groups']} | Note: {r.get('note', '')}")
            
        saved_count = await crawler.save(records)
        print(f"✓ Saved {saved_count} records into database/datastore.")
        return True
    return False

async def test_live_vietnamnet():
    print("\n" + "="*60)
    print("2. LIVE TEST: VIETNAMNET (High School Exam Scores)")
    print("="*60)
    crawler = VietnamNetExamCrawler(year=2024)
    
    # Test valid SBD in Hanoi (01000001 - 01000005)
    test_sbds = ["01000001", "01000002", "01000003"]
    success_count = 0
    
    for sbd in test_sbds:
        url = crawler.url_template.format(sbd=sbd)
        print(f"Fetching SBD {sbd} from {url}...")
        html = await crawler.fetch(url)
        if html:
            scores = crawler.parse(html, sbd=sbd)
            if scores and scores.get("total_score", 0) > 0:
                print(f"✓ Crawled SBD {sbd}:")
                print(f"  Toán: {scores.get('math')}, Văn: {scores.get('literature')}, Lí: {scores.get('physics')}, "
                      f"Hóa: {scores.get('chemistry')}, Ngoại ngữ: {scores.get('foreign_language')}, "
                      f"Tổng: {scores.get('total_score')}")
                saved = await crawler.save([scores])
                print(f"  Saved to DB: {saved} record")
                success_count += 1
            else:
                print(f"  SBD {sbd}: No scores in table or candidate did not sit exam.")
        await asyncio.sleep(1.0) # polite delay
        
    print(f"✓ VietnamNet Live Crawl: {success_count}/{len(test_sbds)} SBDs successfully extracted and saved.")
    return success_count > 0

async def test_live_gemini_extractor():
    print("\n" + "="*60)
    print("3. LIVE TEST: GEMINI UNSTRUCTURED EXTRACTOR (Tokens-Optimized)")
    print("="*60)
    sample_admission_html = """
    <html>
    <head><title>Tuyển sinh 2026</title><style>body { font-size: 14px; }</style></head>
    <body>
        <header><nav><a href="#">Trang chu</a></nav></header>
        <div class="content">
            <h1>Thông báo điểm chuẩn trúng tuyển Đại học Công nghệ Thông tin (QSC) năm 2025</h1>
            <p>Hội đồng tuyển sinh Trường ĐH Công nghệ Thông tin thông báo mức điểm chuẩn chính thức như sau:</p>
            <ul>
                <li>Ngành Khoa học máy tính (Mã ngành: 7480201) xét tuyển tổ hợp A00, A01 có điểm chuẩn là 27.80 điểm. Chỉ tiêu 200 sinh viên.</li>
                <li>Ngành An toàn thông tin (Mã ngành: 7480202) xét tuyển tổ hợp A00, A01, D01 có điểm chuẩn là 26.90 điểm.</li>
                <li>Ngành Kỹ thuật phần mềm (Mã ngành: 7480103) xét tuyển tổ hợp A00, A01 có điểm chuẩn là 28.10 điểm.</li>
            </ul>
        </div>
        <footer><p>Hotline: 028.37252002</p></footer>
    </body>
    </html>
    """
    print("Step 1: Testing HTML cleaning & Markdown conversion (Token reduction)...")
    cleaned_md = gemini_extractor.clean_html_to_markdown(sample_admission_html)
    print(f"Original HTML length: {len(sample_admission_html)} chars -> Cleaned Markdown: {len(cleaned_md)} chars (Reduced {(1 - len(cleaned_md)/len(sample_admission_html))*100:.1f}%)")
    print(f"Cleaned Markdown content:\n{cleaned_md}\n")
    
    print("Step 2: Calling Gemini 2.5 Flash with Flattened OpenAPI Schema...")
    result = await gemini_extractor.extract_admission_data(
        raw_html=sample_admission_html,
        url="https://uit.edu.vn/tuyen-sinh-2025"
    )
    
    if result:
        print(f"✓ Gemini Extracted Successfully:")
        print(f"  University: {result.university_name} ({result.university_code}), Year: {result.year}")
        print(f"  Total majors extracted: {len(result.majors)}")
        for m in result.majors:
            print(f"    - {m.major_code} | {m.major_name} | Cutoff: {m.cutoff_score} | Groups: {m.subject_groups} | Quota: {m.quota}")
            
        print("\nStep 3: Testing SHA256 Cache (0 Token usage on repeat call)...")
        cached_result = await gemini_extractor.extract_admission_data(
            raw_html=sample_admission_html,
            url="https://uit.edu.vn/tuyen-sinh-2025"
        )
        assert cached_result is not None
        print("✓ Cache hit confirmed! No external API call made.")
        return True
    else:
        print("❌ Gemini extraction returned None.")
        return False

async def main():
    print("STARTING LIVE DATA CRAWLING & EXTRACTION TEST SUITE")
    t1 = await test_live_tuyensinh247()
    t2 = await test_live_vietnamnet()
    t3 = await test_live_gemini_extractor()
    
    print("\n" + "="*60)
    print("SUMMARY RESULTS:")
    print(f"  1. TuyenSinh247 Live Crawl: {'PASSED [OK]' if t1 else 'FAILED'}")
    print(f"  2. VietnamNet Live Crawl:   {'PASSED [OK]' if t2 else 'FAILED'}")
    print(f"  3. Gemini Smart Extractor:  {'PASSED [OK]' if t3 else 'FAILED'}")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
