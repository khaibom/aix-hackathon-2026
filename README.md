# 🤖 AI-Powered Proposal Reviewer

AIx × SIVIHACK 2026 — turning AI into solutions for real-world challenges

An intelligent system that analyzes RFP proposals using AI agents to provide comprehensive scoring, gap analysis, and improvement suggestions.

## ✨ Features

- **📄 PDF & Markdown Support**: Upload proposals and RFPs in PDF or Markdown format
- **🤖 AI Agent Pipeline**: 5 specialized agents (Segmenter, Requirement Extractor, Gap Mapper, Scorer, Rewriter)
- **⚖️ Customizable Scoring**: Adjust evaluation criteria with presets (Balanced, Compliance-Focused, Innovation-Focused, Risk-Aware)
- **📊 Detailed Analysis**: Requirement coverage, risk signals, overpromise detection, and actionable improvements
- **🎯 Real-time Progress**: Track analysis progress through each pipeline stage
- **💡 Smart Suggestions**: AI-generated rewrite recommendations for weak sections

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Make start script executable
chmod +x start.sh

# Run the setup and start script
./start.sh
```

The script will:
1. Install all dependencies
2. Create environment files
3. Start backend (port 8000) and frontend (port 5173)

### Option 2: Manual Setup

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI or Gemini API key

## 🔧 Configuration

### Backend (.env)
```env
GEMINI_API_KEY=your_api_key_here
LLM_MODEL=gemini-1.5-flash
```

### Frontend (.env)
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_USE_REAL_API=true
```

## 📁 Project Structure

```
aix-hackathon-2026/
├── src/
│   ├── backend/              # FastAPI backend
│   │   ├── app/
│   │   │   ├── agents/       # AI agents
│   │   │   ├── routers/      # API endpoints
│   │   │   ├── utils/        # Document parser (PDF support)
│   │   │   └── main.py
│   │   └── requirements.txt
│   │
│   └── fe/                   # React frontend
│       ├── src/
│       │   ├── lib/          # API client
│       │   ├── types/        # TypeScript definitions
│       │   ├── hooks/        # React hooks
│       │   └── routes/       # UI components
│       └── package.json
│
├── hackathon/                # Sample data and documentation
├── DEPLOYMENT.md            # Detailed deployment guide
└── start.sh                 # Quick start script
```

## 🧪 Testing with Sample Data

Sample files are in `hackathon/challenge/sample_data/`:
- `rfp_nordframe.md` - Example RFP
- `response_1_weak.md` - Low quality proposal
- `response_2_medium.md` - Medium quality proposal
- `response_3_strong.md` - High quality proposal
- `response_4_overpromise.md` - Overpromising proposal

## 🎯 Usage Example

1. **Start Services**: `./start.sh`
2. **Open Frontend**: http://localhost:5173
3. **Upload Files**: RFP + Proposal (PDF or Markdown)
4. **Customize Criteria**: Select preset or adjust weights
5. **Analyze**: Wait 30-60 seconds
6. **Review Results**: Scores, gaps, and improvements

## 📊 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/health` | Health check |
| `/audit/run-full-pipeline-files` | **Full analysis with file upload** ⭐ |
| `/audit/segment` | Segment proposal |
| `/audit/extract-requirements` | Extract RFP requirements |
| `/audit/map-gaps` | Map gaps |
| `/audit/score` | Score proposal |
| `/audit/rewrite` | Generate improvements |

Full API docs: http://localhost:8000/docs

## 🐛 Troubleshooting

**Backend won't start:**
```bash
# Check port and API key
lsof -ti:8000 | xargs kill -9
cat src/backend/.env
```

**Frontend can't connect:**
```bash
# Verify backend health
curl http://localhost:8000/health
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for more details.

## 🚀 Ready to Ship!

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)

---

Built with FastAPI, React, TanStack Router, and Google Gemini AI
