#!/bin/bash

# 🚀 Quick Start Script for AI-Powered Proposal Reviewer
# This script starts both backend and frontend servers

set -e

echo "🚀 Starting AI-Powered Proposal Reviewer..."
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if backend .env exists
if [ ! -f "src/backend/.env" ]; then
    echo -e "${YELLOW}⚠️  Backend .env not found${NC}"
    echo "Creating from .env.example..."
    cp src/backend/.env.example src/backend/.env
    echo -e "${RED}❗ Please edit src/backend/.env and add your GEMINI_API_KEY${NC}"
    echo "Then run this script again."
    exit 1
fi

# Check if frontend .env exists
if [ ! -f "src/fe/.env" ]; then
    echo -e "${YELLOW}⚠️  Frontend .env not found${NC}"
    echo "Creating from .env.example..."
    cp src/fe/.env.example src/fe/.env
    echo -e "${GREEN}✅ Created src/fe/.env${NC}"
fi

# Check if Python dependencies are installed
echo -e "${BLUE}📦 Checking backend dependencies...${NC}"
cd src/backend
if ! python -c "import pypdf" 2>/dev/null; then
    echo -e "${YELLOW}Installing backend dependencies...${NC}"
    pip install -r requirements.txt
fi
cd ../..

# Check if Node dependencies are installed
echo -e "${BLUE}📦 Checking frontend dependencies...${NC}"
cd src/fe
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    npm install
fi
cd ../..

echo ""
echo -e "${GREEN}✅ All dependencies installed${NC}"
echo ""
echo -e "${BLUE}🚀 Starting services...${NC}"
echo ""

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down services...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}
trap cleanup EXIT INT TERM

# Start backend
echo -e "${BLUE}🔧 Starting backend on http://localhost:8000${NC}"
cd src/backend
uvicorn app.main:app --reload --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
cd ../..

# Wait for backend to start
echo "Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend is ready${NC}"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Backend failed to start. Check src/backend/backend.log${NC}"
        exit 1
    fi
done

# Start frontend
echo -e "${BLUE}💻 Starting frontend on http://localhost:5173${NC}"
cd src/fe
npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!
cd ../..

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 Services are running!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}🔧 Backend:${NC}  http://localhost:8000"
echo -e "${BLUE}📚 API Docs:${NC} http://localhost:8000/docs"
echo -e "${BLUE}💻 Frontend:${NC} http://localhost:5173"
echo ""
echo -e "${YELLOW}📝 Logs:${NC}"
echo "   Backend:  src/backend/backend.log"
echo "   Frontend: src/fe/frontend.log"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Keep script running and show logs
tail -f src/backend/backend.log src/fe/frontend.log
