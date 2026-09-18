# AI-Powered Proposal Reviewer

AIx × SIVIHACK 2026 — Agentic AI Proposal Evaluation & Review Assistant

---

## 1. Sản phẩm là gì?

**AI-Powered Proposal Reviewer** là hệ thống AI đa tác tử (Agentic Pipeline) tự động phân tích và thẩm định bản thảo hồ sơ thầu (Proposal) dựa trên yêu cầu từ hồ sơ mời thầu (RFP). Hệ thống đóng vai trò như một chuyên gia đánh giá thầu cấp cao (senior reviewer), cung cấp phản hồi khách quan, có trích dẫn minh chứng và có tính hành động cao trước khi gửi đến khách hàng.

### Kiến trúc Pipeline 5 Agents:
1. **Segmenter (`segmenter.py`)**: Tách cấu trúc tài liệu RFP và Draft proposal theo đoạn văn, heading, bullet point có định danh và định vị vị trí (không tốn LLM token). Hỗ trợ Markdown, TXT và PDF.
2. **Requirement Extractor (`requirement_extractor.py`)**: Trích xuất toàn diện tất cả yêu cầu (Technical, Functional, Budget, Timeline, SLA, Risk) kèm phân loại mức độ quan trọng (`hard` / `soft`) và trích dẫn `source_segment_ids`.
3. **Gap & Compliance Mapper (`gap_mapper.py`)**: So khớp và đánh giá mức độ đáp ứng từng yêu cầu (`met`, `weak`, `missing`), trích xuất minh chứng đối ứng (`matched_segment_ids`) và lý do chi tiết (`rationale`).
4. **Scorer (`scorer.py`)**: Đánh giá theo bộ tiêu chuẩn 7 tiêu chí (Appendix A). Tính điểm `Completeness` một cách tất định (deterministic) dựa trên tỷ lệ đáp ứng, kết hợp LLM chấm điểm 6 tiêu chí định tính còn lại. Hỗ trợ tái tính điểm tức thì (`/rescore`) khi người dùng điều chỉnh trọng số.
5. **Rewriter (`rewriter.py`)**: Tự động sinh nội dung viết lại (rewrite suggestions) cụ thể, khả thi cho các yêu cầu bị đánh giá `weak` hoặc `missing` dựa trên dữ liệu thực tế từ RFP (không dùng placeholder chung chung).

---

## 2. Hướng dẫn set up và chạy demo

### Yêu cầu hệ thống
- **Python**: 3.11 trở lên
- **Google Gemini API Key**

### Bước 1: Cài đặt Dependencies

Sử dụng `pip` hoặc `uv`:

```bash
# Cách 1: Sử dụng pip
cd src/backend
pip install -r requirements.txt

# Cách 2: Sử dụng uv (tối ưu tốc độ)
uv sync
```

### Bước 2: Cấu hình Environment

Tạo file `.env` tại `src/backend/.env`:

```bash
cp src/backend/.env.example src/backend/.env
```

Cập nhật khóa API vào file `src/backend/.env`:
```env
GEMINI_API_KEY=your_google_gemini_api_key_here
```

### Bước 3: Khởi chạy Backend API Server

```bash
cd src/backend
uvicorn app.main:app --reload --port 8000
```

- **API Server**: http://localhost:8000
- **Tài liệu Swagger UI tương tác**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Bước 4: Chạy Demo Pipeline

Chạy script kiểm thử pipeline tự động với bộ dữ liệu mẫu:

```bash
# Chạy toàn bộ test suite
pytest src/backend/tests -v

# Chạy test kiểm thử trích xuất và phân tích tài liệu PDF
python test_pdf.py
```

#### Demo quy trình gọi API qua cURL:

```bash
# 1. Tạo session
SESSION_ID=$(curl -s -X POST http://localhost:8000/audit/session | jq -r '.session_id')

# 2. Phân đoạn tài liệu (Segmentation)
curl -X POST "http://localhost:8000/audit/session/$SESSION_ID/segment" \
  -H "Content-Type: application/json" \
  -d '{
    "rfp_text": "# Requirements\n1. Web dashboard\n2. PostgreSQL integration",
    "draft_text": "# Proposal\nWe provide a web dashboard."
  }'

# 3. Trích xuất yêu cầu (Extract Requirements)
curl -X POST "http://localhost:8000/audit/session/$SESSION_ID/extract-requirements"

# 4. Đánh giá khoảng cách đáp ứng (Gap Mapping)
curl -X POST "http://localhost:8000/audit/session/$SESSION_ID/map-compliance"

# 5. Chấm điểm (Scoring)
curl -X POST "http://localhost:8000/audit/session/$SESSION_ID/score"

# 6. Tạo đề xuất viết lại (Rewriter)
curl -X POST "http://localhost:8000/audit/session/$SESSION_ID/rewrite"
```

---

## 3. Công nghệ sử dụng

| Phân tầng | Công nghệ | Mục đích |
|---|---|---|
| **Ngôn ngữ** | Python 3.11+ | Nền tảng cốt lõi backend |
| **Web Framework** | FastAPI (≥0.111), Uvicorn (≥0.29) | REST API bất đồng bộ hiệu năng cao |
| **Mô hình AI / LLM** | Google Gemini (1.5 Flash / Pro) | Xử lý ngôn ngữ tự nhiên, trích xuất yêu cầu, phân tích khoảng cách và đề xuất viết lại |
| **SDK AI** | `google-genai` (≥1.0) | SDK chính thức từ Google, hỗ trợ Structured JSON Outputs |
| **Data Validation** | Pydantic v2 | Kiểm thực kiểu dữ liệu và định dạng Schema đầu vào / đầu ra |
| **Xử lý tài liệu** | PyPDF (`pypdf` ≥4.0.0) | Trích xuất nội dung văn bản từ các tệp PDF |
| **Kiểm thử** | pytest (≥8), httpx (≥0.27) | Unit testing, Integration testing và E2E testing |

---

## 4. Dataset / API / Core-library / Template đã sử dụng

### 1. APIs & SDKs:
- **Google Gemini API** (`google-genai`): Tích hợp qua `app/services/llm_client.py` với cơ chế ép kiểu Pydantic Schema đảm bảo dữ liệu phản hồi luôn hợp lệ.

### 2. Core Libraries:
- `fastapi`, `uvicorn`, `pydantic`, `pypdf`, `python-dotenv`, `httpx`, `pytest`.

### 3. Dataset & Dữ liệu mẫu (`hackathon/challenge/sample_data/`):
- `rfp_nordframe.md`: Hồ sơ mời thầu chuẩn của khách hàng doanh nghiệp vận tải NordFrame Logistics GmbH.
- `response_1_weak.md`: Đề xuất chất lượng kém (nội dung chung chung, thiếu kế hoạch giá và tiến độ).
- `response_2_medium.md`: Đề xuất mức độ trung bình (đáp ứng chức năng nhưng thiếu công khai rủi ro và giá mập mờ).
- `response_3_strong.md`: Đề xuất chất lượng cao (đáp ứng toàn diện, rõ ràng và minh bạch).
- `response_4_overpromise.md`: Đề xuất hứa hẹn quá mức (vượt phạm vi, mâu thuẫn ràng buộc kỹ thuật).
- `sample_pdfs/`: Các bản dựng PDF tương ứng phục vụ kiểm thử tính năng đọc định dạng PDF.

---

## 5. Giới hạn hiện tại của sản phẩm (Optional)

1. **Quản lý Session In-Memory**: Trạng thái phiên kiểm tra (`AuditState`) hiện lưu trong bộ nhớ RAM của tiến trình FastAPI, phù hợp cho môi trường prototype / demo, sẽ được chuyển sang Redis/PostgreSQL khi triển khai môi trường phân tán.
2. **Xử lý PDF dạng ảnh quét (Scanned/OCR)**: Trích xuất PDF hiện hỗ trợ tài liệu kỹ thuật số có text layer (digital PDF); các tài liệu scan hoàn toàn bằng hình ảnh cần bổ sung pipeline OCR (Tesseract / Vision AI).
3. **Giới hạn Rate Limit LLM**: Các bước gọi LLM phụ thuộc vào quota RPM/TPM của Gemini API Key. Pipeline đã được tối ưu hóa theo mô hình batching để giảm số lượng API calls tối đa.

