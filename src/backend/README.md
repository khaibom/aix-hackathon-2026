# AI-Powered Proposal Reviewer — Backend

Agentic RAG pipeline that audits a draft proposal against an RFP and returns structured feedback: requirements extracted, compliance gaps flagged, scores, and rewrite suggestions.

## Sản phẩm là gì?

Backend FastAPI cho hệ thống tự động review proposal bằng AI. Pipeline gồm 5 agent (Segmenter → Requirement Extractor → Gap/Compliance Mapper → Scorer → Rewriter) dùng chung một `AuditState` JSON duy nhất.

## Công nghệ sử dụng

| Layer | Công nghệ |
|---|---|
| API | Python 3.11+, FastAPI, Uvicorn |
| Schema | Pydantic v2 |
| LLM | Google Gemini 1.5 Flash (dev) / Pro (demo) via `google-genai` SDK |
| Config | python-dotenv |
| Test | pytest + httpx TestClient |

## Dataset / API / Core library

- **google-genai ≥ 1.0** — official Gemini SDK (structured JSON output support)
- Sample data: `hackathon/challenge/sample_data/` — fictional RFPs and proposals provided by the hackathon organisers

## Cài đặt & Chạy demo

```bash
# 1. Clone và vào thư mục backend
cd src/backend

# 2. Cài dependencies
pip install -r requirements.txt

# 3. Tạo file .env
cp .env.example .env
# Điền GEMINI_API_KEY=<your key> vào .env

# 4. Chạy server
uvicorn app.main:app --reload
# → http://localhost:8000
# → Swagger UI: http://localhost:8000/docs
```

## Test

```bash
cd src/backend
pytest
```

## API nhanh

```bash
# Tạo session mới
curl -X POST http://localhost:8000/audit/session
# → {"session_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}

# Xem trạng thái session
curl http://localhost:8000/audit/session/<session_id>

# Ping Gemini (kiểm tra tích hợp end-to-end)
curl -X POST http://localhost:8000/audit/session/<session_id>/llm-ping
# → {"text": "pong"}

# Health check
curl http://localhost:8000/health
# → {"status": "ok"}
```

## Giới hạn hiện tại (Sprint 0)

- Session lưu in-memory — mất khi restart server.
- Chưa có logic agent nào — chỉ scaffold và contract.
- Không có auth, không có database, không có Docker.

## Sprint 1: Segmentation & Requirement Extraction

**1. Phân rã Document (Segmenter)**
Chạy logic tách RFP và Draft proposal (không dùng LLM):
```bash
curl -X POST http://localhost:8000/audit/session/<session_id>/segment \
  -H "Content-Type: application/json" \
  -d '{"rfp_text": "# 1. Scope\nPara", "draft_text": "# Draft\nHello"}'
```

**2. Trích xuất Yêu cầu (Requirement Extractor)**
Dùng LLM (Gemini) để đọc RFP và rút trích các yêu cầu:
```bash
curl -X POST http://localhost:8000/audit/session/<session_id>/extract-requirements
```

**Chạy Test cho Sprint 1:**
```bash
# Chạy unit tests nhanh (không tốn phí API)
pytest -m "not integration"

# Chạy full integration test (gọi API thật)
pytest -m integration
```

## Sprint 2: Gap/Compliance Mapper

**3. Đánh giá Mức độ Đáp ứng (Gap Mapper)**
Dùng LLM (Gemini) để so khớp các yêu cầu (từ Sprint 1) với bản thảo draft proposal, tìm ra các lỗ hổng:

### Endpoint

```bash
curl -X POST http://localhost:8000/audit/session/<session_id>/map-compliance
```

**Yêu cầu tiên quyết:** Session phải có:
- `requirements` (từ `/extract-requirements`)
- `draft_segments` (từ `/segment`)

**Response:** Danh sách `ComplianceResult` với các trường:
- `req_id`: ID của requirement từ RFP
- `status`: `"met"` (đáp ứng), `"weak"` (đáp ứng yếu/mơ hồ), hoặc `"missing"` (thiếu)
- `matched_segment_ids`: Danh sách ID các đoạn draft hỗ trợ đánh giá (rỗng nếu `missing`)
- `rationale`: Giải thích 1-2 câu, trích dẫn/paraphrase đoạn text thực tế

### Complete Workflow Example

Quy trình hoàn chỉnh từ đầu đến cuối cho Sprint 1 + Sprint 2:

```bash
# Bước 1: Tạo session mới
SESSION_ID=$(curl -s -X POST http://localhost:8000/audit/session | jq -r '.session_id')
echo "Session ID: $SESSION_ID"

# Bước 2: Phân đoạn RFP và Draft proposal
curl -X POST "http://localhost:8000/audit/session/$SESSION_ID/segment" \
  -H "Content-Type: application/json" \
  -d '{
    "rfp_text": "# Requirements\n1. Web dashboard\n2. PostgreSQL integration\n3. Role-based access",
    "draft_text": "# Proposal\nWe will build a cloud dashboard with secure login."
  }'

# Bước 3: Trích xuất requirements từ RFP
curl -X POST "http://localhost:8000/audit/session/$SESSION_ID/extract-requirements"

# Bước 4: Đánh giá compliance (Gap Mapping)
curl -X POST "http://localhost:8000/audit/session/$SESSION_ID/map-compliance"
```

### Example Response

```json
[
  {
    "req_id": "req_000",
    "status": "missing",
    "matched_segment_ids": [],
    "rationale": "RFP requires PostgreSQL integration with no migration; draft segment draft_002 only mentions 'cloud dashboard' without confirming this constraint."
  },
  {
    "req_id": "req_001",
    "status": "weak",
    "matched_segment_ids": ["draft_003"],
    "rationale": "RFP asks for role-based access with manager vs HQ split; draft segment draft_003 says 'secure login for different users' but doesn't specify the two-tier split."
  },
  {
    "req_id": "req_002",
    "status": "met",
    "matched_segment_ids": ["draft_002", "draft_005"],
    "rationale": "RFP requires web-based dashboard; draft segments draft_002 and draft_005 clearly describe a 'cloud-based dashboard displaying inventory data in real time'."
  }
]
```

### Status Meanings

- **`met`**: Draft proposal clearly and specifically addresses the requirement với concrete evidence
- **`weak`**: Draft mentions the requirement vaguely, partially, hoặc generically (không đủ chi tiết)
- **`missing`**: Draft không đề cập đến requirement, hoặc defers it (e.g., "pricing will be provided later", "TBD")

**Lưu ý quan trọng:** Khi status là `"missing"`, `matched_segment_ids` luôn là mảng rỗng `[]`.

### Design Rationale: Full-Context Grounding (No Vector Search)

Sprint 2 sử dụng kiến trúc **full-context grounding** thay vì Retrieval-Augmented Generation (RAG) với vector search. Đây là lựa chọn có chủ đích:

**Tại sao không dùng Vector Search?**
- RFP và proposal thông thường chỉ dài 2-10 trang (≈ 5,000-25,000 tokens)
- Gemini hỗ trợ context window lên tới 1M+ tokens
- Ở quy mô này, passing toàn bộ draft vào context đảm bảo:
  - **Độ chính xác cao hơn**: LLM thấy toàn bộ context, không bỏ sót requirements
  - **Tránh phân mảnh ngữ cảnh**: Vector search có thể retrieve các đoạn sai hoặc thiếu context
  - **Đơn giản hơn**: Không cần embedding model, vector database, hoặc similarity tuning

**Khi nào cần Vector Search?**
- Khi documents rất lớn (> 100 trang, > 100k tokens)
- Khi cần search trong knowledge base với hàng ngàn documents

Đối với use case này (single RFP vs single proposal), full-context grounding là optimal choice.

### Troubleshooting

#### Error: "requirements is empty - call /extract-requirements first"
**Nguyên nhân:** Session chưa có requirements.
**Giải pháp:** Chạy `/extract-requirements` trước khi gọi `/map-compliance`:
```bash
curl -X POST "http://localhost:8000/audit/session/$SESSION_ID/extract-requirements"
```

#### Error: "draft_segments is empty - call /segment with draft_text first"
**Nguyên nhân:** Session chưa có draft segments.
**Giải pháp:** Chạy `/segment` với cả `rfp_text` và `draft_text`:
```bash
curl -X POST "http://localhost:8000/audit/session/$SESSION_ID/segment" \
  -H "Content-Type: application/json" \
  -d '{"rfp_text": "...", "draft_text": "..."}'
```

#### Error: "502 LLM service error: ..."
**Nguyên nhân:** Gemini API call thất bại (network, quota, hoặc API key).
**Giải pháp:**
1. Kiểm tra `GEMINI_API_KEY` trong file `.env`
2. Verify API key còn valid và chưa hết quota: https://aistudio.google.com/apikey
3. Retry request (có built-in retry logic nhưng có thể fail sau 3 attempts)
4. Kiểm tra Gemini API status: https://status.cloud.google.com/

#### Warning: "Estimated tokens (950000) approaching context limit (1M)"
**Nguyên nhân:** Document quá lớn, gần đạt giới hạn context window.
**Giải pháp:**
- Xem xét chia proposal thành nhiều phần nhỏ hơn
- Hoặc summarize các phần không quan trọng trước khi đưa vào LLM
- Nếu cần xử lý documents rất lớn, consider chuyển sang RAG architecture với vector search

#### ValueError: "requirements list cannot be empty" / "draft_segments list cannot be empty"
**Nguyên nhân:** Internal validation error (không nên xảy ra nếu workflow đúng).
**Giải pháp:** Đảm bảo gọi các endpoints theo đúng thứ tự: `/segment` → `/extract-requirements` → `/map-compliance`

**Chạy Test cho Sprint 2:**
```bash
# Unit tests (nhanh, mock LLM)
pytest tests/test_gap_mapper.py -v

# Integration test (gọi API thật, ~30s)
pytest tests/test_gap_mapper_integration.py -v -m integration

# Full test suite
pytest -v  # All tests except integration
pytest -v -m integration  # Only integration tests
```

## Sprint 3: Scoring & Rewriting

**4. Đánh giá Proposal (Scorer)**
Đánh giá bản thảo proposal theo bộ 7 tiêu chí cố định, với tiêu chí "Completeness vs. RFP Requirements" được tính toán deterministic từ compliance_map (không qua LLM):

### Bộ 7 tiêu chí cố định (Fixed Rubric)

1. **Problem Understanding** (1-5): Draft có phản ánh đúng vấn đề/mục tiêu thực tế của client (từ RFP) không?
2. **Scope & Deliverables Clarity** (1-5): Các deliverable có cụ thể và rõ ràng không?
3. **Pricing Clarity** (1-5): Giá có được nêu rõ ràng và phân tách chi tiết không?
4. **Timeline Clarity** (1-5): Các milestone và ngày tháng có cụ thể không?
5. **Completeness vs. RFP Requirements** (1-5): Draft có đáp ứng mọi yêu cầu của RFP không? **Tính toán deterministic** từ compliance_map.
6. **Tone & Persuasiveness** (1-5): Có tự tin, tập trung vào client, chuyên nghiệp không?
7. **Risk/Assumptions Transparency** (1-5): Các giả định/phụ thuộc/rủi ro có được nêu rõ không?

### Công thức tính Completeness (Deterministic)

```python
completeness_ratio = (met_count + 0.5 * weak_count) / total_requirements
score_1to5 = round(1 + completeness_ratio * 4)  # Maps 0..1 → 1..5
```

Công thức này đảm bảo tính reproducibility - cùng compliance_map luôn cho cùng điểm Completeness.

### Endpoints

#### POST /audit/session/{id}/score
Đánh giá proposal với weights tùy chọn. Lưu vào session.

```bash
# Score với equal weights (mặc định)
curl -X POST "http://localhost:8000/audit/session/$SESSION_ID/score"

# Score với custom weights
curl -X POST "http://localhost:8000/audit/session/$SESSION_ID/score" \
  -H "Content-Type: application/json" \
  -d '{
    "weights": {
      "Problem Understanding": 0.2,
      "Scope & Deliverables Clarity": 0.15,
      "Pricing Clarity": 0.15,
      "Timeline Clarity": 0.15,
      "Completeness vs. RFP Requirements": 0.2,
      "Tone & Persuasiveness": 0.1,
      "Risk/Assumptions Transparency": 0.05
    }
  }'
```

**Yêu cầu tiên quyết:** `compliance_map`, `requirements`, `draft_segments` phải tồn tại.

**Response format:**
```json
{
  "scores": [
    {
      "criterion": "Problem Understanding",
      "score_1to5": 3,
      "comment": "States the general problem correctly but only at surface level",
      "weight": 0.142857,
      "weighted_score": 0.428571
    },
    {
      "criterion": "Completeness vs. RFP Requirements",
      "score_1to5": 2,
      "comment": "1 of 9 requirements fully met, 1 weakly addressed, 7 missing.",
      "weight": 0.142857,
      "weighted_score": 0.285714
    }
    ...
  ],
  "overall": 1.71
}
```

**Lưu ý quan trọng:**
- `Completeness vs. RFP Requirements` được tính toán từ compliance_map counts, KHÔNG phải LLM đánh giá
- 6 tiêu chí còn lại được LLM đánh giá trong 1 batch call duy nhất
- Nếu weights không đầy đủ, các tiêu chí thiếu sẽ được điền bằng 1/7 và normalize về tổng = 1.0

#### POST /audit/session/{id}/rewrite
Tạo gợi ý rewrite cụ thể cho các requirement "weak" và "missing" (bỏ qua "met").

```bash
curl -X POST "http://localhost:8000/audit/session/$SESSION_ID/rewrite"
```

**Response format:**
```json
[
  {
    "req_id": "req_000",
    "original_text": null,
    "suggested_text": "We will integrate with your existing PostgreSQL inventory database with zero migration required. Our solution connects directly to your current database schema, preserving all existing data and workflows.",
    "insertion_point": "Add a new 'Technical Architecture' section after 'Our Approach'"
  },
  {
    "req_id": "req_002",
    "original_text": "Secure login for different users",
    "suggested_text": "Role-based access control: warehouse managers will see only their assigned site's inventory, while HQ staff will have visibility across all 6 warehouses.",
    "insertion_point": "Replace existing text in the Features section"
  }
]
```

**Đặc điểm:**
- Chỉ tạo suggestion cho requirement có status "weak" hoặc "missing"
- `original_text`: null nếu missing, text hiện tại nếu weak
- `suggested_text`: Văn bản cụ thể, dùng chi tiết thực tế từ RFP (VD: €80k-120k, PostgreSQL, 3 months)
- **KHÔNG có placeholder** như "[insert pricing]", "TBD", hoặc "[add details]"
- Validation: retry một lần nếu LLM trả về placeholder, raise 502 nếu vẫn fail

#### POST /audit/session/{id}/rescore ⚡ INSTANT (No LLM)
Tính lại weighted scores với weights mới. **Miễn phí và tức thì** - thiết kế cho frontend weight sliders.

```bash
curl -X POST "http://localhost:8000/audit/session/$SESSION_ID/rescore" \
  -H "Content-Type: application/json" \
  -d '{
    "weights": {
      "Problem Understanding": 0.25,
      "Scope & Deliverables Clarity": 0.15,
      "Pricing Clarity": 0.1,
      "Timeline Clarity": 0.1,
      "Completeness vs. RFP Requirements": 0.25,
      "Tone & Persuasiveness": 0.1,
      "Risk/Assumptions Transparency": 0.05
    }
  }'
```

**Đặc điểm quan trọng:**
- **KHÔNG gọi LLM** - chỉ đọc scores đã lưu và tính lại weighted_score
- **KHÔNG lưu** vào session - chỉ trả về kết quả computed
- Response time: **<50ms** (thay vì ~10-30s nếu có LLM call)
- Yêu cầu: **TẤT CẢ 7 weights** phải được cung cấp
- Use case: Frontend sliders điều chỉnh weights real-time

### Design Rationale

**Tại sao Completeness là deterministic?**
- Đảm bảo reproducibility: cùng compliance_map → cùng score
- Grounding vào kết quả phân tích thực tế (compliance mapping)
- Giảm LLM variance cho tiêu chí quan trọng này
- Công thức rõ ràng, kiểm tra được: (met + 0.5*weak) / total

**Tại sao /rescore là instant?**
- Frontend weight sliders cần feedback real-time
- /rescore chỉ đọc stored scores, tính lại weighted_score
- Không có LLM call = <50ms response, zero API cost
- Workflow: gọi /score 1 lần, sau đó /rescore bao nhiêu lần cũng được

**Tại sao Rewriter chỉ xử lý weak/missing?**
- "Met" requirements đã OK, không cần rewrite
- Tập trung vào gaps thực sự cần fix
- Tiết kiệm LLM cost và response time
- Output ngắn gọn, actionable hơn

### Complete Workflow Example

```bash
# Setup (Sprint 1+2)
SESSION_ID=$(curl -s -X POST http://localhost:8000/audit/session | jq -r '.session_id')

curl -X POST "http://localhost:8000/audit/session/$SESSION_ID/segment" \
  -H "Content-Type: application/json" \
  -d '{"rfp_text": "...", "draft_text": "..."}'

curl -X POST "http://localhost:8000/audit/session/$SESSION_ID/extract-requirements"
curl -X POST "http://localhost:8000/audit/session/$SESSION_ID/map-compliance"

# Sprint 3: Scoring & Rewriting
# Bước 1: Score với equal weights
RESULT=$(curl -s -X POST "http://localhost:8000/audit/session/$SESSION_ID/score")
echo $RESULT | jq '.overall'  # e.g., 1.71

# Bước 2: Generate rewrites
curl -X POST "http://localhost:8000/audit/session/$SESSION_ID/rewrite" | jq '.[].req_id'

# Bước 3: Rescore với weights khác nhau (instant, miễn phí)
curl -X POST "http://localhost:8000/audit/session/$SESSION_ID/rescore" \
  -H "Content-Type: application/json" \
  -d '{
    "weights": {
      "Problem Understanding": 0.3,
      "Scope & Deliverables Clarity": 0.1,
      "Pricing Clarity": 0.1,
      "Timeline Clarity": 0.1,
      "Completeness vs. RFP Requirements": 0.3,
      "Tone & Persuasiveness": 0.05,
      "Risk/Assumptions Transparency": 0.05
    }
  }' | jq '.overall'  # Điểm mới với weights khác
```

### Troubleshooting

#### Error: "compliance_map is empty - call /map-compliance first"
**Nguyên nhân:** Chưa chạy Sprint 2 gap mapping.
**Giải pháp:** 
```bash
curl -X POST "http://localhost:8000/audit/session/$SESSION_ID/map-compliance"
```

#### Error: "scores is empty - call /score first before rescoring"
**Nguyên nhân:** Chưa chạy /score lần nào.
**Giải pháp:**
```bash
curl -X POST "http://localhost:8000/audit/session/$SESSION_ID/score"
```

#### Error: "Missing weights for criteria: [...]"
**Nguyên nhân:** /rescore yêu cầu đầy đủ 7 weights.
**Giải pháp:** Cung cấp weights cho tất cả 7 tiêu chí (tổng không nhất thiết phải = 1.0, sẽ được normalize tự động).

#### Error: "502 LLM service error: Rewrite validation failed..."
**Nguyên nhân:** LLM trả về placeholder text sau 2 lần retry.
**Giải pháp:** Retry request. Nếu vẫn fail, có thể do prompt phức tạp quá hoặc RFP thiếu chi tiết cụ thể.

**Chạy Test cho Sprint 3:**
```bash
# Unit tests (scorer logic, <1s)
pytest tests/test_scorer.py -v

# Integration tests (real API calls, ~30-60s)
pytest tests/test_scorer_integration.py -v -m integration
pytest tests/test_rewriter_integration.py -v -m integration
pytest tests/test_sprint3_e2e.py -v -m integration

# Full suite
pytest -v  # Unit tests only
pytest -v -m integration  # All integration tests
```
