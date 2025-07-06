# Context-Aware RAG System with Student Authentication

## Overview

This system implements a **context-aware RAG (Retrieval-Augmented Generation)** system with **student authentication** and **admin portal** for university document management. The system provides personalized responses based on student department and semester, with secure authentication and document management capabilities.

## System Architecture

### Components

1. **FastAPI Backend** (`server/`) - Core RAG engine with authentication
2. **Next.js Frontend** (`next-frontend/`) - Student chat interface
3. **Streamlit Admin Portal** (`portal/`) - Document and student management
4. **SQLite Database** - Student and session management

### Authentication Flow

```
Student Registration (Admin Portal) → Student Login (Frontend) → Context-Aware Chat
```

## Features

### 🔐 Authentication System
- **Simple Student Authentication**: Roll number as username and password
- **JWT Token Management**: Secure session handling
- **Admin Portal**: Student registration without complex admin passwords
- **Automatic Redirects**: Seamless login/logout flow

### 📚 Context-Aware RAG
- **Student Context Integration**: Responses filtered by department and semester
- **Document Metadata Filtering**: Smart document selection based on student profile
- **Personalized Prompts**: Context-aware system prompts
- **Real-time Streaming**: Live chat responses

### 🎛️ Admin Portal
- **Document Management**: Upload, edit, delete PDFs with metadata
- **Student Registration**: Add students with department/semester info
- **Session Tracking**: Monitor portal activities
- **Form Auto-clear**: Efficient batch student registration

## Technical Implementation

### Backend Structure

```
server/
├── main.py              # FastAPI app with RAG endpoints
├── auth.py              # JWT authentication utilities
├── database.py          # SQLite database operations
├── config.py            # System configuration
├── models.py            # Pydantic models
├── utils.py             # Utility functions
├── research_agent.py    # Research mode functionality
└── routes/
    ├── auth.py          # Authentication endpoints
    └── research.py      # Research mode endpoints
```

### Frontend Structure

```
next-frontend/
├── app/
│   ├── page.js          # Main chat interface
│   ├── login/
│   │   ├── page.js      # Login page
│   │   └── login.css    # Login styles
│   └── api/
│       ├── auth/
│       │   └── login/
│       │       └── route.js  # Login API proxy
│       ├── chat/
│       │   └── route.js      # Chat API proxy
│       └── research/
│           └── route.js      # Research API proxy
├── contexts/
│   └── AuthContext.js   # Authentication context
└── components/
    └── ResearchPlan.js  # Research plan component
```

### Database Schema

```sql
-- Students table
CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_no VARCHAR(20) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL,
    branch VARCHAR(100) NOT NULL,
    semester VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API Endpoints

### Authentication
- `POST /auth/login` - Student login
- `POST /auth/students/register` - Register new student (admin)
- `GET /auth/students` - Get all students (admin)

### Chat & RAG
- `POST /chat/stream` - Context-aware chat with streaming
- `POST /update_knowledge_base` - Update document index

### Research Mode
- `POST /research/plan` - Generate research plan
- `POST /research/execute` - Execute research plan
- `POST /research/stream` - Stream research results

## Configuration

### Environment Variables
```python
# server/config.py
MODEL_NAME = "llama3.2:3b"           # Ollama model
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHAT_TEMPERATURE = 0.7
CHAT_CONTEXT_SIZE = 4096
GPU_LAYERS = 35
BATCH_SIZE = 8
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
```

### System Prompts
- **Context-Aware Prompt**: Includes student department, semester, and academic level
- **Document Filtering**: Prioritizes documents matching student's department and semester
- **Markdown Formatting**: Structured responses with proper formatting

## Usage Guide

### For Administrators

1. **Start the Portal**:
   ```bash
   cd portal
   streamlit run app.py
   ```

2. **Register Students**:
   - Navigate to "Register Students"
   - Fill in student details (roll number, name, department, branch, semester)
   - Click "Register Student"
   - Form auto-clears for next student

3. **Manage Documents**:
   - Upload PDFs with metadata
   - Edit document properties
   - Delete outdated documents

### For Students

1. **Access the System**:
   - Open the Next.js frontend
   - Navigate to login page

2. **Login**:
   - Use roll number as both username and password
   - System automatically redirects to chat

3. **Chat Interface**:
   - Ask questions about course materials
   - Responses are personalized based on your department/semester
   - Use research mode for complex queries

## Security Features

### Authentication
- **JWT Tokens**: Secure session management
- **Simple Password System**: Roll number as password (configurable)
- **Token Verification**: Automatic token validation on protected routes

### Data Protection
- **Context Filtering**: Students only see relevant documents
- **Input Validation**: Server-side validation of all inputs
- **Error Handling**: Graceful error responses

## Performance Optimizations

### Backend
- **Connection Pooling**: Optimized Ollama connections
- **Embedding Caching**: Cached document embeddings
- **Async Processing**: Non-blocking I/O operations
- **Context-Aware Retrieval**: Smart document filtering

### Frontend
- **Streaming Responses**: Real-time chat updates
- **Optimized Renders**: Efficient React state management
- **Lazy Loading**: On-demand component loading

## Error Handling

### Common Issues
1. **Login Failures**: Check roll number and password match
2. **Document Access**: Ensure documents are uploaded with correct metadata
3. **Model Issues**: Verify Ollama is running with correct model

### Debugging
- **Backend Logs**: Check `ingestion_log.txt`
- **Frontend Console**: Browser developer tools
- **Database**: Direct SQLite access for troubleshooting

## Future Enhancements

### Planned Features
- **Role-Based Access**: Different access levels for students/faculty
- **Advanced Analytics**: Usage tracking and insights
- **Multi-Modal Support**: Image and video document processing
- **Real-time Collaboration**: Shared chat sessions

### Scalability
- **Database Migration**: PostgreSQL for production
- **Load Balancing**: Multiple backend instances
- **CDN Integration**: Static asset optimization
- **Microservices**: Modular service architecture

## Development Setup

### Prerequisites
- Python 3.8+
- Node.js 18+
- Ollama with llama3.2:3b model
- SQLite

### Installation
```bash
# Backend
pip install -r requirements.txt

# Frontend
cd next-frontend
npm install

# Portal
pip install streamlit
```

### Running the System
```bash
# Start backend
python -m server.main

# Start frontend
cd next-frontend
npm run dev

# Start portal
cd portal
streamlit run app.py
```

## Contributing

### Code Standards
- **Python**: PEP 8 compliance
- **JavaScript**: ESLint configuration
- **Documentation**: Comprehensive docstrings
- **Testing**: Unit tests for critical functions

### Development Workflow
1. Feature branch creation
2. Code review process
3. Testing and validation
4. Documentation updates
5. Deployment checklist

---

**Last Updated**: December 2024  
**Version**: 2.0 (Context-Aware with Authentication)  
**Maintainer**: RAG System Team 