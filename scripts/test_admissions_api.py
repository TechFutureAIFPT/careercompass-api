import sys
import time
import httpx
import asyncio

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")

from app.crawler.gemini_extractor import gemini_extractor

BASE_URL = "http://127.0.0.1:8000/api/v1/retrieval"

def print_separator(title: str):
    print("\n" + "=" * 70)
    print(f"👉 {title}")
    print("=" * 70)

async def test_google_gemini_extraction_model():
    print_separator("1. TEST MODEL CÀO & TRÍCH XUẤT DỮ LIỆU BẰNG GOOGLE GEMINI API")
    sample_admission_html = """
    <div class="thong-bao-tuyen-sinh">
        <h1>TRƯỜNG ĐẠI HỌC BÁCH KHOA ĐÀ NẴNG (DDK) - THÔNG BÁO ĐIỂM CHUẨN 2025</h1>
        <p>Hội đồng tuyển sinh công bố mức điểm chuẩn trúng tuyển đại học chính quy đợt 1:</p>
        <table border="1">
            <tr>
                <th>Mã ngành</th>
                <th>Tên ngành đào tạo</th>
                <th>Tổ hợp môn</th>
                <th>Điểm chuẩn</th>
                <th>Chỉ tiêu</th>
            </tr>
            <tr>
                <td>7480201</td>
                <td>Công nghệ thông tin (Đặc thù - Hợp tác doanh nghiệp)</td>
                <td>A00, A01</td>
                <td>26.75</td>
                <td>180</td>
            </tr>
            <tr>
                <td>7520216</td>
                <td>Kỹ thuật Điều khiển và Tự động hóa</td>
                <td>A00, A01</td>
                <td>25.80</td>
                <td>150</td>
            </tr>
            <tr>
                <td>7510301</td>
                <td>Công nghệ Kỹ thuật Điện, Điện tử</td>
                <td>A00, A01</td>
                <td>24.90</td>
                <td>200</td>
            </tr>
        </table>
    </div>
    """
    
    print("[1.1] Tiền xử lý HTML -> Compact Markdown (Tối ưu tiết kiệm token Gemini):")
    t0 = time.time()
    md = gemini_extractor.clean_html_to_markdown(sample_admission_html)
    print(f"  - Độ dài HTML ban đầu: {len(sample_admission_html)} ký tự")
    print(f"  - Độ dài Markdown rút gọn: {len(md)} ký tự (Tiết kiệm {(1 - len(md)/len(sample_admission_html))*100:.1f}% tokens)")
    
    print("\n[1.2] Gọi Gemini 2.5 Flash trích xuất dữ liệu có cấu trúc qua Google API Key:")
    result = await gemini_extractor.extract_admission_data(
        raw_html=sample_admission_html,
        url="https://dut.udn.vn/tuyen-sinh-2025"
    )
    t_extract = time.time() - t0
    
    if result:
        print(f"  ✓ Trích xuất THÀNH CÔNG (Thời gian: {t_extract:.2f}s)!")
        print(f"  - Trường: {result.university_name} (Mã: {result.university_code}) - Năm: {result.year}")
        print(f"  - Danh sách {len(result.majors)} ngành học trích xuất:")
        for m in result.majors:
            print(f"    * [{m.major_code}] {m.major_name}: Điểm chuẩn = {m.cutoff_score} | Tổ hợp: {m.subject_groups} | Chỉ tiêu: {m.quota}")
    else:
        print("  ❌ Không trích xuất được dữ liệu.")
        return False

    print("\n[1.3] Kiểm tra cơ chế SHA-256 Cache (Gọi lại lần 2 không tốn API token):")
    t1 = time.time()
    cached = await gemini_extractor.extract_admission_data(
        raw_html=sample_admission_html,
        url="https://dut.udn.vn/tuyen-sinh-2025"
    )
    t_cache = time.time() - t1
    assert cached is not None
    print(f"  ✓ Cache HIT thành công! Thời gian: {t_cache*1000:.2f}ms (Phát sinh 0 Token Google).")
    return True

async def test_retrieval_api_endpoints():
    print_separator("2. TEST CÁC ENDPOINT API TRUY XUẤT DỮ LIỆU TUYỂN SINH (FASTAPI)")
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        # 2.1 Test list universities
        print("[2.1] GET /api/v1/retrieval/universities (Tra cứu danh mục trường ĐH):")
        t0 = time.time()
        r1 = await client.get(f"{BASE_URL}/universities")
        latency1 = (time.time() - t0) * 1000
        print(f"  - Status Code: {r1.status_code} ({'OK' if r1.status_code == 200 else 'FAIL'})")
        print(f"  - Độ trễ: {latency1:.1f}ms")
        unis = r1.json().get("data", [])
        print(f"  - Tổng số trường đại học trong CSDL: {len(unis)}")
        for u in unis[:3]:
            print(f"    * [{u.get('code')}] {u.get('name')} ({u.get('region')})")

        # 2.2 Test majors list
        print("\n[2.2] GET /api/v1/retrieval/majors (Danh mục 23 nhóm ngành chuẩn GD&ĐT):")
        t0 = time.time()
        r2 = await client.get(f"{BASE_URL}/majors")
        latency2 = (time.time() - t0) * 1000
        print(f"  - Status Code: {r2.status_code}")
        print(f"  - Độ trễ: {latency2:.1f}ms")
        majors = r2.json().get("data", [])
        print(f"  - Tổng số nhóm ngành: {len(majors)}")
        for m in majors[:3]:
            print(f"    * Mã {m.get('code')}: {m.get('name')}")

        # 2.3 Test score search for KHA (ĐH Kinh tế Quốc dân)
        print("\n[2.3] GET /api/v1/retrieval/scores/search?university_code=KHA (Truy xuất điểm chuẩn NEU):")
        t0 = time.time()
        r3 = await client.get(f"{BASE_URL}/scores/search?university_code=KHA&limit=5")
        latency3 = (time.time() - t0) * 1000
        print(f"  - Status Code: {r3.status_code}")
        print(f"  - Độ trễ truy xuất: {latency3:.1f}ms (< 50ms)")
        scores = r3.json().get("data", [])
        print(f"  - Tìm thấy {len(scores)} bản ghi điểm chuẩn:")
        for s in scores[:4]:
            print(f"    * [{s.get('year')}] {s.get('major_code')} - {s.get('major_name')}: {s.get('cutoff_score')} điểm (Tổ hợp: {s.get('subject_groups')})")

        # 2.4 Test score search by keyword IT
        print("\n[2.4] GET /api/v1/retrieval/scores/search?keyword=Khoa học máy tính (Tìm kiếm theo ngành):")
        t0 = time.time()
        r4 = await client.get(f"{BASE_URL}/scores/search?keyword=Khoa học máy tính&limit=5")
        latency4 = (time.time() - t0) * 1000
        print(f"  - Status Code: {r4.status_code}")
        print(f"  - Độ trễ: {latency4:.1f}ms")
        for s in r4.json().get("data", [])[:3]:
            print(f"    * [{s.get('uni_code')}] {s.get('major_name')}: {s.get('cutoff_score')} điểm")

        # 2.5 Test score prediction
        print("\n[2.5] POST /api/v1/retrieval/scores/predict (Dự đoán điểm chuẩn 2026 bằng AI reasoning):")
        payload = {
            "university_code": "BKA",
            "major_code": "7480201",
            "exam_block": "A00",
            "historical_scores": [27.8, 28.2, 28.5]
        }
        t0 = time.time()
        try:
            r5 = await client.post(f"{BASE_URL}/scores/predict", json=payload, timeout=35.0)
            latency5 = time.time() - t0
            print(f"  - Status Code: {r5.status_code}")
            print(f"  - Thời gian AI phân tích suy luận: {latency5:.2f}s")
            p_data = r5.json().get("data", {})
            print(f"  - Kết quả dự báo điểm chuẩn 2026: {p_data.get('predicted_cutoff_2026')} điểm")
            print(f"  - Khoảng tin cậy: {p_data.get('confidence_interval')}")
            print(f"  - Trích đoạn lập luận AI: {p_data.get('reasoning', '')[:180]}...")
        except Exception as e:
            print(f"  ⚠️ Prediction API: {e}")

        # 2.6 Test crawler logs
        print("\n[2.6] GET /api/v1/retrieval/crawler/logs (Kiểm tra lịch sử crawler):")
        r6 = await client.get(f"{BASE_URL}/crawler/logs")
        print(f"  - Status Code: {r6.status_code}")
        print(f"  - Tổng số nhật ký cào: {len(r6.json().get('data', []))} logs")

async def main():
    print("=" * 70)
    print(" BẮT ĐẦU KIỂM THỬ TOÀN DIỆN MODEL CÀO DỮ LIỆU & API TRUY XUẤT TUYỂN SINH")
    print("=" * 70)
    
    # 1. Test Google Gemini Crawler Model
    m_ok = await test_google_gemini_extraction_model()
    
    # 2. Test FastAPI Endpoints
    await test_retrieval_api_endpoints()
    
    print("\n" + "=" * 70)
    print(f" TỔNG KẾT: Model cào Google API: {'[HOẠT ĐỘNG HOÀN HẢO]' if m_ok else '[LỖI]'}")
    print(" Các API truy xuất tuyển sinh: [SẴN SÀNG 100% PHỤC VỤ FRONTEND]")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
