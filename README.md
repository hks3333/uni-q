# RAG n Roll: University RAG Chatbot System

## 🚀 Installation & Setup (Windows)

### 1. Clone the Repository
```
git clone <repo-url>
cd rag_n_roll
```

### 2. Create and Activate Python Virtual Environment (in root)
```
python -m venv venv
venv\Scripts\activate
```

### 3. Install Python Backend Requirements
```
pip install -r requirements.txt
```

### 4. Install Node.js Frontend Dependencies
```
cd next-frontend
npm install
cd ..
```

### 5. Start the Full System
```
run_new.bat
```
This will:
- Start Ollama (LLM server)
- Start FastAPI backend
- Start Next.js frontend
- Open the browser to the chat UI

---

# 🧠 System Overview

This project is a full-stack, context-aware RAG (Retrieval-Augmented Generation) chatbot for university students and admins. It features:
- **Contextual RAG**: Answers are based on university documents, filtered by student department and semester.
- **Admin Portal**: Register students, manage documents.
- **Student Login**: JWT-based authentication, simple roll number/password.
- **Personalized Chat**: Student context is used in every prompt and document retrieval.
- **Query Classification**: Distinguishes between general and RAG queries for optimal LLM usage.
- **Research Mode**: Advanced research planning and synthesis for complex queries.

## 🔑 Authentication
- Students log in with roll number and password (default: roll number).
- JWT tokens are issued and stored in the browser.
- Tokens include student context (department, semester, etc.) and are used for all API requests.

## 📚 RAG Flow
- Student asks a question in chat.
- Query is classified as GENERAL or RAG (using fast keyword/LLM logic).
- For RAG queries:
  - Documents are filtered by department/semester.
  - Top relevant chunks are retrieved from FAISS index.
  - Prompt is constructed with context and student info.
  - LLM (Ollama) generates a markdown-formatted answer.
  - Source PDFs are linked at the end.
- For GENERAL queries:
  - LLM answers using only general knowledge and student context.

## 🛠️ Tech Stack
- **Backend**: FastAPI, LangChain, FAISS, PyMuPDF, Ollama, PyJWT, Tavily (research)
- **Frontend**: Next.js, React, Tailwind CSS, React-Markdown
- **Database**: SQLite (students, sessions)
- **LLM**: Ollama (Llama3.2 or compatible)

## 📝 Document Management
- PDFs and metadata are stored in `/documents`.
- Admins can update the knowledge base via the portal.
- FAISS index is rebuilt as needed.

## 🧑‍💻 Development Notes
- All prompt templates are centralized in `server/config.py`.
- All classification logic is centralized in `server/utils.py`.
- No dead code or redundant endpoints.

## 🆘 Troubleshooting
- If ports are in use, use the stop option in `run_new.bat` to kill all services.
- For LLM issues, ensure Ollama is running and the model is downloaded.
- For frontend issues, ensure Node.js 18+ is installed.

---

**Enjoy your personalized, context-aware university chatbot!**
