# 🚀 Deployment Guide: AI-Powered Proposal Reviewer

Complete guide to deploy the backend API with PDF support and frontend integration.

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- npm or bun
- OpenAI/Gemini API key

## 🔧 Backend Setup

### 1. Install Dependencies

```bash
cd src/backend

# Install Python dependencies
pip install -r requirements.txt

# Or using uv (recommended)
uv pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your API key
nano .env
```

Add your API key:
```env
GEMINI_API_KEY=your_api_key_here
LLM_MODEL=gemini-1.5-flash
```

### 3. Start Backend Server

```bash
# Using uvicorn
uvicorn app.main:app --reload --port 8000

# Or using uv
uv run uvicorn app.main:app --reload --port 8000
```

Backend will be available at: **http://localhost:8000**
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

---

## 💻 Frontend Setup

### 1. Install Dependencies

```bash
cd src/fe

# Using npm
npm install

# Or using bun
bun install
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env
```

The `.env` file should contain:
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_USE_REAL_API=true
```

### 3. Start Frontend

```bash
# Using npm
npm run dev

# Or using bun
bun run dev
```

Frontend will be available at: **http://localhost:5173**

---

## 🧪 Testing the Integration

### 1. Backend Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "ok"}
```

### 2. Test PDF Upload Endpoint

```bash
curl -X POST http://localhost:8000/audit/run-full-pipeline-files \
  -F "session_id=test_session_123" \
  -F "rfp_file=@hackathon/challenge/sample_data/rfp_nordframe.md" \
  -F "proposal_file=@hackathon/challenge/sample_data/response_3_strong.md"
```

### 3. Frontend End-to-End Test

1. Open http://localhost:5173
2. Upload RFP file (PDF or Markdown)
3. Upload Proposal file (PDF or Markdown)
4. Adjust criteria weights (optional)
5. Click "Analyze Proposal"
6. Wait for analysis (30-60 seconds)
7. Review results

### 4. Test with Sample Data

Sample files are located in: `hackathon/challenge/sample_data/`

- **RFP**: `rfp_nordframe.md`
- **Responses**:
  - `response_1_weak.md` (should score <70)
  - `response_2_medium.md` (should score 60-80)
  - `response_3_strong.md` (should score >75)
  - `response_4_overpromise.md` (low Risk Transparency score)

---

## 📁 File Structure

```
aix-hackathon-2026/
├── src/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── agents/          # AI agents (segmenter, scorer, etc.)
│   │   │   ├── routers/         # API endpoints
│   │   │   ├── utils/           # Document parser (NEW)
│   │   │   │   └── document_parser.py
│   │   │   └── main.py
│   │   ├── requirements.txt     # Python dependencies (UPDATED)
│   │   └── .env
│   │
│   └── fe/
│       ├── src/
│       │   ├── lib/
│       │   │   └── api-client.ts      # API client (NEW)
│       │   ├── types/
│       │   │   └── api.ts             # TypeScript types (NEW)
│       │   ├── hooks/
│       │   │   └── useProposalAnalysis.ts  # React hooks (NEW)
│       │   └── routes/
│       │       └── index.tsx          # Main UI (TO UPDATE)
│       ├── .env.example           # Environment config (NEW)
│       └── package.json
│
└── hackathon/challenge/sample_data/  # Test files
```

---

## 🐛 Troubleshooting

### Backend Issues

**Error: "PDF support not available"**
```bash
pip install pypdf>=4.0.0
```

**Error: "Module not found: app.utils"**
```bash
# Ensure __init__.py exists
ls src/backend/app/utils/__init__.py
```

**Error: "GEMINI_API_KEY not found"**
```bash
# Check .env file
cat src/backend/.env
```

### Frontend Issues

**Error: "Cannot connect to server"**
- Ensure backend is running on port 8000
- Check `VITE_API_BASE_URL` in `.env`

**Error: "VITE_USE_REAL_API is not defined"**
```bash
# Create .env from example
cp .env.example .env
```

**CORS errors**
- Backend should allow `http://localhost:5173` by default
- Check `app/main.py` CORS configuration

### Network Issues

**Port 8000 already in use**
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn app.main:app --reload --port 8001
# Update VITE_API_BASE_URL=http://localhost:8001
```

---

## 🔄 Development Workflow

### Typical Development Session

```bash
# Terminal 1 - Backend
cd src/backend
uv run uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
cd src/fe
npm run dev

# Terminal 3 - Testing
cd src/backend
pytest tests/test_stress_all_samples.py -v
```

### Making Changes

**Backend Changes:**
1. Edit Python files in `src/backend/app/`
2. Server auto-reloads (--reload flag)
3. Test with `curl` or Swagger UI

**Frontend Changes:**
1. Edit TypeScript files in `src/fe/src/`
2. Vite auto-reloads
3. Test in browser

---

## 📊 Performance Notes

- **First Request**: May take 10-15s (cold start)
- **Subsequent Requests**: 30-60s per analysis
- **Timeout**: 30s per agent operation
- **Max File Size**: 50MB per file
- **Supported Formats**: PDF, Markdown (.md), Text (.txt)

---

## 🚀 Production Deployment

### Backend (FastAPI)

```bash
# Install production server
pip install gunicorn

# Run with gunicorn
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

### Frontend (React)

```bash
# Build for production
npm run build

# Preview build
npm run preview

# Deploy build/ directory to:
# - Vercel
# - Netlify
# - AWS S3 + CloudFront
# - Any static hosting
```

### Environment Variables (Production)

Backend:
```env
GEMINI_API_KEY=<production_key>
LLM_MODEL=gemini-1.5-pro  # Use pro for production
CORS_ORIGINS=https://your-frontend-domain.com
```

Frontend:
```env
VITE_API_BASE_URL=https://your-backend-domain.com
VITE_USE_REAL_API=true
```

---

## 📝 API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/audit/segment` | POST | Segment proposal (text) |
| `/audit/extract-requirements` | POST | Extract requirements from RFP (text) |
| `/audit/map-gaps` | POST | Map gaps between RFP and proposal |
| `/audit/score` | POST | Score proposal |
| `/audit/rewrite` | POST | Generate improvement suggestions |
| `/audit/segment-file` | POST | Segment proposal (file upload) |
| `/audit/extract-requirements-file` | POST | Extract requirements (file upload) |
| `/audit/run-full-pipeline` | POST | Full pipeline (text input) |
| `/audit/run-full-pipeline-files` | POST | **Full pipeline (file upload)** ⭐ |

---

## ✅ Success Checklist

- [ ] Backend running on port 8000
- [ ] Frontend running on port 5173
- [ ] `.env` files configured correctly
- [ ] Health check returns `{"status": "ok"}`
- [ ] Sample file analysis completes successfully
- [ ] Scores show expected ordering (strong > medium > weak)
- [ ] PDF files upload and parse correctly
- [ ] Markdown files upload and parse correctly
- [ ] Error messages display properly
- [ ] Progress indicators work during analysis

---

## 🎉 Ready to Ship!

Your AI-Powered Proposal Reviewer is now fully integrated with:
✅ PDF and Markdown file support
✅ Dual file upload (RFP + Proposal)
✅ Enhanced criteria editor with presets and sliders
✅ Real-time progress tracking
✅ Complete error handling
✅ Type-safe API integration

**Next Steps:**
1. Test with your own RFP and proposal files
2. Customize criteria presets for your use case
3. Deploy to production when ready
4. Monitor API usage and performance

---

## 📧 Support

For issues or questions:
- Check `/docs` endpoint for API documentation
- Review error logs in terminal
- Test with sample data first
- Verify environment variables

**Happy shipping! 🚀**
