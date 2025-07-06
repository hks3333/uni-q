# RAG Mode - Complete Flow Documentation

## Overview
This document explains the complete flow of what happens when a user sends a query in **normal RAG mode** (document-based chat). The system retrieves relevant information from uploaded documents and generates contextual responses.

## User Input → Output Flow

### 1. **Frontend: User Interface (next-frontend/app/page.js)**
- **Component**: `ChatPage` function
- **User Action**: Types message in chat input and presses Enter
- **Trigger**: `sendMessage()` function is called
- **Decision**: `researchMode` is `false`, so `handleRegularQuery()` is executed

### 2. **Frontend: Message Processing (next-frontend/app/page.js)**
- **Function**: `handleRegularQuery(userMessage)`
- **Actions**:
  - Creates `AbortController` for request cancellation
  - Adds user message to chat history immediately
  - Creates empty bot message placeholder
  - Prepares request payload: `{ question: userMessage }`

### 3. **Frontend API Route: Chat Proxy (next-frontend/app/api/chat/route.js)**
- **File**: `next-frontend/app/api/chat/route.js`
- **Function**: `POST` handler
- **Actions**:
  - Receives request from frontend
  - Forwards request to FastAPI backend at `http://localhost:8000/chat/stream`
  - Creates streaming response back to frontend
  - Handles error responses and status codes

### 4. **Backend: FastAPI Server (server/main.py)**
- **File**: `server/main.py`
- **Component**: FastAPI application with mounted routers
- **Action**: Routes request to chat endpoint

### 5. **Backend: Chat Route Handler (server/routes/chat.py)**
- **File**: `server/routes/chat.py` (implied from main.py structure)
- **Function**: Chat stream endpoint
- **Actions**:
  - Receives chat request with question
  - Processes document retrieval and response generation
  - Returns streaming response

### 6. **Backend: Document Processing & Retrieval**
- **Components Involved**:
  - **FAISS Index**: Searches for relevant document chunks
  - **Embedding Model**: `all-MiniLM-L6-v2` (HuggingFace)
  - **Document Store**: Local FAISS index in `faiss_index/` directory
  - **Chunk Processing**: Documents split into 512-token chunks with 128-token overlap

### 7. **Backend: Context Retrieval**
- **Process**:
  - User question is embedded using HuggingFace model
  - FAISS performs similarity search against document chunks
  - Top relevant chunks are retrieved based on semantic similarity
  - Retrieved chunks are combined into context for LLM

### 8. **Backend: LLM Processing (Ollama Integration)**
- **Model**: `llama3.2:latest`
- **Configuration**:
  - Context window: 8K tokens
  - Temperature: 0.4
  - GPU layers: 50
- **Process**:
  - System prompt is formatted with retrieved context
  - User question is added to prompt
  - Request sent to Ollama API at `http://localhost:11434/api/generate`
  - Streaming response is generated

### 9. **Backend: Response Streaming**
- **Format**: JSON streaming response from Ollama
- **Structure**: Each chunk contains `{ "response": "text", "done": false }`
- **Processing**: Response text is extracted and streamed back

### 10. **Frontend: Response Handling (next-frontend/app/page.js)**
- **Function**: `handleRegularQuery()` (continued)
- **Process**:
  - Receives streaming response from API
  - Uses `ReadableStream` to process chunks
  - Updates bot message content in real-time
  - Handles `AbortError` for cancellation
  - Handles network errors with user-friendly messages

### 11. **Frontend: UI Updates**
- **Components**:
  - Message list updates with streaming text
  - Auto-scroll to bottom on new messages
  - Loading state management
  - Error state display
- **User Experience**: Real-time streaming response with typing effect

## Key Files Involved

### Frontend Files
- `next-frontend/app/page.js` - Main chat interface and logic
- `next-frontend/app/chat.css` - Chat-specific styling
- `next-frontend/app/globals.css` - Global styling
- `next-frontend/app/api/chat/route.js` - API proxy to backend

### Backend Files
- `server/main.py` - FastAPI application entry point
- `server/routes/chat.py` - Chat endpoint handlers
- `server/models.py` - Pydantic data models
- `server/config.py` - Configuration settings
- `server/utils.py` - Utility functions for document processing

### Data Storage
- `faiss_index/` - Vector index for document chunks
- `embed_cache/` - Cached embeddings for performance
- `documents/` - Original uploaded documents

## Configuration Parameters

### Model Settings
- **Embedding Model**: `all-MiniLM-L6-v2`
- **LLM Model**: `llama3.2:latest`
- **Chat Context Size**: 8,192 tokens
- **Chunk Size**: 512 tokens
- **Chunk Overlap**: 128 tokens
- **Temperature**: 0.4
- **GPU Layers**: 50

### System Behavior
- **Streaming**: Real-time response generation
- **Error Handling**: Graceful fallbacks and user notifications
- **Cancellation**: Support for request cancellation
- **Auto-scroll**: Automatic chat scrolling to latest message

## Error Handling

### Network Errors
- Connection failures to Ollama
- FastAPI server unavailability
- Frontend-backend communication issues

### Processing Errors
- Document retrieval failures
- Embedding generation errors
- LLM response generation failures

### User Experience
- Clear error messages
- Retry mechanisms
- Graceful degradation

## Performance Considerations

### Caching
- Embedding cache for repeated queries
- FAISS index optimization
- Document chunk caching

### Streaming
- Real-time response generation
- Progressive UI updates
- Memory-efficient processing

### Scalability
- Modular architecture
- Separate frontend/backend services
- Configurable model parameters 