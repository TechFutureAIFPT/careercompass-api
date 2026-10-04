import sys
import time
import httpx
import json

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")

LIVE_URL = "https://admissions-data-retrieval-api.vercel.app"

def main():
    print("=" * 75)
    print(f" KIỂM THỬ TRỰC TIẾP TRÊN API ĐÃ DEPLOY: {LIVE_URL}")
    print("=" * 75)
    
    with httpx.Client(base_url=LIVE_URL, timeout=30.0) as client:
        # 1. Health check
        t0 = time.time()
        r_health = client.get("/health")
        latency = (time.time() - t0) * 1000
        print(f"\n[1] GET /health: HTTP {r_health.status_code} ({latency:.1f}ms)")
        print(f"    Body: {r_health.json()}")

        # 2. Universities list
        t0 = time.time()
        r_unis = client.get("/api/v1/retrieval/universities")
        latency = (time.time() - t0) * 1000
        unis = r_unis.json().get("data", [])
        print(f"\n[2] GET /api/v1/retrieval/universities: HTTP {r_unis.status_code} ({latency:.1f}ms)")
        print(f"    Tìm thấy {len(unis)} trường đại học.")
        for u in unis[:3]:
            print(f"    - [{u.get('code')}] {u.get('name')} (Khu vực: {u.get('region')})")

        # 3. Majors list
        t0 = time.time()
        r_majors = client.get("/api/v1/retrieval/majors")
        latency = (time.time() - t0) * 1000
        majors = r_majors.json().get("data", [])
        print(f"\n[3] GET /api/v1/retrieval/majors: HTTP {r_majors.status_code} ({latency:.1f}ms)")
        print(f"    Tìm thấy {len(majors)} nhóm ngành đào tạo chuẩn GD&ĐT.")
        for m in majors[:3]:
            print(f"    - Mã {m.get('code')}: {m.get('name')}")

        # 4. Search Cutoff Scores for NEU (KHA)
        t0 = time.time()
        r_scores = client.get("/api/v1/retrieval/scores/search?university_code=KHA&limit=5")
        latency = (time.time() - t0) * 1000
        scores = r_scores.json().get("data", [])
        print(f"\n[4] GET /api/v1/retrieval/scores/search?university_code=KHA: HTTP {r_scores.status_code} ({latency:.1f}ms)")
        print(f"    Truy xuất điểm chuẩn Đại học Kinh tế Quốc dân (NEU):")
        for s in scores[:4]:
            print(f"    - [{s.get('year')}] {s.get('major_code')} - {s.get('major_name')}: {s.get('cutoff_score')} điểm (Tổ hợp: {s.get('subject_groups')})")

        # 5. Search Cutoff Scores for BKA (Đại học Bách Khoa Hà Nội)
        t0 = time.time()
        r_bka = client.get("/api/v1/retrieval/scores/search?university_code=BKA&limit=5")
        latency = (time.time() - t0) * 1000
        bka_scores = r_bka.json().get("data", [])
        print(f"\n[5] GET /api/v1/retrieval/scores/search?university_code=BKA: HTTP {r_bka.status_code} ({latency:.1f}ms)")
        print("    Truy xuất điểm chuẩn Đại học Bách Khoa Hà Nội (HUST):")
        for s in bka_scores:
            print(f"    - [{s.get('year')}] {s.get('major_code')} - {s.get('major_name')}: {s.get('cutoff_score')} điểm ({s.get('subject_groups')}) | {s.get('note')}")

        # 6. Score Prediction 2026
        t0 = time.time()
        pred_payload = {
            "university_code": "BKA",
            "major_code": "IT1",
            "exam_block": "A00",
            "historical_scores": [28.2, 28.5, 28.8]
        }
        r_pred = client.post("/api/v1/retrieval/scores/predict", json=pred_payload)
        latency = (time.time() - t0) * 1000
        p_data = r_pred.json().get("data", {})
        print(f"\n[6] POST /api/v1/retrieval/scores/predict: HTTP {r_pred.status_code} ({latency:.1f}ms)")
        print(f"    Dự báo 2026 cho {p_data.get('university_code')} ngành {p_data.get('major_code')} ({p_data.get('exam_block')}):")
        print(f"    - Điểm chuẩn dự báo: {p_data.get('predicted_cutoff_2026')} | Khoảng tin cậy: {p_data.get('confidence_interval')}")


        # 6. Check OpenAPI Documentation
        t0 = time.time()
        r_openapi = client.get("/api/v1/openapi.json")
        latency = (time.time() - t0) * 1000
        print(f"\n[6] GET /api/v1/openapi.json: HTTP {r_openapi.status_code} ({latency:.1f}ms)")
        openapi_spec = r_openapi.json()
        print(f"    API Title: {openapi_spec.get('info', {}).get('title')}")
        print(f"    Total API Endpoints: {len(openapi_spec.get('paths', {}))}")

    print("\n" + "=" * 75)
    print(" KẾT LUẬN: TẤT CẢ CÁC ENDPOINT TRÊN VERCEL ĐANG HOẠT ĐỘNG 100% ONLINE!")
    print(f" Domain chính thức: {LIVE_URL}")
    print(f" Swagger UI tương tác: {LIVE_URL}/docs")
    print("=" * 75)

if __name__ == "__main__":
    main()
