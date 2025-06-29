# RAG & Roll - Local RAG System with Research Agent

A complete local Retrieval-Augmented Generation (RAG) system with integrated research capabilities, featuring a FastAPI backend, Next.js frontend, and Streamlit admin portal.

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+**
- **Node.js 16+**
- **Ollama** (for local LLM)
- **Tavily API Key** (for web research)

### 1. Install Ollama
```bash
# Download from https://ollama.ai/
# Or use winget on Windows:
winget install Ollama.Ollama
```

### 2. Pull Llama3.2 Model
```bash
ollama pull llama3.2:latest
```

### 3. Get Tavily API Key
- Visit [Tavily](https://tavily.com/)
- Sign up for free API key
- Create `.env` file in project root:
```
TAVILY_API_KEY=your_api_key_here
```

### 4. Start Everything
```bash
# Windows
run_new.bat

# Or manually:
# 1. Activate venv: venv\Scripts\activate
# 2. Start Ollama: ollama serve
# 3. Start FastAPI: python -m uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
# 4. Start Next.js: cd next-frontend && npm run dev
```

## 📁 Project Structure

```
rag_n_roll/
├── server/                 # FastAPI backend
│   ├── main.py            # Main server entry point
│   ├── models.py          # Pydantic models
│   ├── config.py          # Configuration settings
│   ├── utils.py           # Utility functions
│   ├── research_agent.py  # Research agent implementation
│   └── routes/            # API routes
├── next-frontend/         # Next.js chat interface
│   ├── app/              # Next.js app directory
│   ├── components/       # React components
│   └── lib/             # Utility libraries
├── frontend/             # Streamlit admin portal
│   └── bot.py           # Admin interface
├── portal/              # Additional portal
│   └── app.py           # Portal application
├── documents/           # Document storage
├── faiss_index/         # Vector index storage
├── embed_cache/         # Embedding cache
├── run_all.bat         # Full system startup
├── run_new.bat         # Quick startup
└── requirements.txt    # Python dependencies
```

## 🔧 Features

### Core RAG System
- **Document Upload & Processing**: Upload PDFs, docs, text files
- **Vector Embeddings**: Using HuggingFace embeddings
- **FAISS Index**: Local vector storage and similarity search
- **Chat Interface**: Modern Next.js chat UI with streaming responses

### Research Agent
- **Research Mode Toggle**: Switch between chat and research modes
- **AI Research Planning**: Generate detailed research plans with Llama3.2
- **Web Search**: Integrated Tavily API for real-time web research
- **Content Synthesis**: AI-powered research synthesis and reporting
- **Streaming Responses**: Real-time research progress and results

### Admin Tools
- **Streamlit Portal**: Document management and system monitoring
- **Batch Processing**: Upload multiple documents at once
- **Index Management**: View and manage vector indices

## 🎯 Usage

### Chat Mode
1. Open http://localhost:3000
2. Type your question
3. Get AI responses based on your uploaded documents

### Research Mode
1. Toggle "Research Mode" in chat interface
2. Enter your research query
3. Review and refine the AI-generated research plan
4. Execute the plan to search the web
5. Get a comprehensive research synthesis

### Admin Portal
1. Open http://localhost:8501
2. Upload documents for RAG system
3. Monitor system status and indices

## ⚙️ Configuration

### Environment Variables (.env)
```
TAVILY_API_KEY=your_tavily_api_key
RESEARCH_MODE_ENABLED=true
MAX_SEARCH_RESULTS=5
RESEARCH_TIMEOUT=300
```

### Model Configuration (server/config.py)
- **Chat Context**: 8K tokens
- **Research Plan**: 8K tokens  
- **Research Synthesis**: 24K tokens
- **GPU Layers**: Configurable for performance

## 🔍 API Endpoints

### Chat
- `POST /chat` - Send chat message
- `POST /chat/stream` - Stream chat response

### Research
- `POST /research/plan` - Generate research plan
- `POST /research/execute` - Execute research plan
- `POST /research/stream` - Stream research synthesis

### Documents
- `POST /upload` - Upload document
- `GET /documents` - List documents
- `DELETE /documents/{id}` - Delete document

## 🛠️ Development

### Backend Development
```bash
cd server
python -m uvicorn main:app --reload --port 8000
```

### Frontend Development
```bash
cd next-frontend
npm install
npm run dev
```

### Testing
```bash
# Test chat functionality
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "history": []}'

# Test research plan generation
curl -X POST http://localhost:8000/research/plan \
  -H "Content-Type: application/json" \
  -d '{"query": "artificial intelligence trends 2024"}'
```

## 🚨 Troubleshooting

### Common Issues

**Ollama not responding:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
ollama serve
```

**Missing dependencies:**
```bash
# Reinstall Python dependencies
pip install -r requirements.txt

# Reinstall Node dependencies
cd next-frontend
npm install
```

**Port conflicts:**
- FastAPI: Change port in `run_new.bat` (default: 8000)
- Next.js: Change port in `next-frontend/package.json` (default: 3000)
- Streamlit: Change port in `frontend/bot.py` (default: 8501)

**Research mode not working:**
- Check Tavily API key in `.env`
- Verify internet connection for web searches
- Check Ollama model availability

### Performance Optimization
- **GPU Acceleration**: Set `GPU_LAYERS` in config.py
- **Context Windows**: Adjust token limits based on your hardware
- **Search Results**: Reduce `MAX_SEARCH_RESULTS` for faster research
- **Cache Management**: Clear `embed_cache/` for fresh embeddings

## 📝 License

This project is for educational and research purposes.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

---

**Happy RAGging! 🎸**
