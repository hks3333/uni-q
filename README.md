# Uni-Q RAG System

A local Retrieval-Augmented Generation (RAG) system for university knowledge bases, featuring:
- Admin PDF upload/metadata portal (Streamlit)
- FastAPI backend for ingestion, chunking, embedding, and retrieval
- Local FAISS vector store for fast semantic search
- Ollama LLM (phi3.5:3.8b) for answer generation
- HuggingFace all-MiniLM-L6-v2 for embeddings
- PDF source citation with direct PDF viewing
- Hybrid chat history (summary-based, optional)

## Models Used
- **LLM:** phi3.5:3.8b (via Ollama, quantized, GPU-accelerated)
- **Embeddings:** all-MiniLM-L6-v2 (HuggingFace, via langchain-huggingface)


## Setup Instructions

### 1. Clone the repository and create a virtual environment
```sh
python -m venv venv
```

### 2. Activate the virtual environment
- **Windows:**
  ```sh
  venv\Scripts\activate
  ```
- **Linux/Mac:**
  ```sh
  source venv/bin/activate
  ```

### 3. Install requirements
```sh
pip install -r requirements.txt
```

### 4. (Optional) Download and set up Ollama
- Download Ollama from [https://ollama.com/](https://ollama.com/) and ensure it is running with the desired model (e.g., `phi3.5:3.8b`).

## How to Run

### **Recommended: Use the provided script**
From the project root, run:
```sh
run_all.bat
```
This will:
- Activate the virtual environment
- Start the FastAPI backend server
- Start the Streamlit chat frontend in a new window

### **Manual Run (if not using script)**
1. Activate the virtual environment:
   ```sh
   venv\Scripts\activate
   ```
2. Start the FastAPI backend:
   ```sh
   uvicorn server.fastapi_ingestion_server:app --reload
   ```
3. In a new terminal, start the chat frontend:
   ```sh
   cd frontend
   streamlit run bot.py
   ```

## Usage

### **Admin Portal**
- Upload PDFs and metadata via the Streamlit portal (`portal/app.py`).
- Edit or delete files and metadata as needed.
- Click "Update Knowledge Base" to process new/updated files and update the FAISS index.

### **Chat Frontend**
- Access the chat UI via the Streamlit app (`frontend/bot.py`).
- Ask questions about the knowledge base. Answers are generated using the LLM and retrieved context.
- Cited PDF sources are shown with a "View PDF" link for direct inspection.

## Citation/Source Feature
- Each answer includes a list of PDF files used as sources.
- Click "View PDF" to open the cited document in a new browser tab.

## Notes
- All data and indexes are stored locally; no cloud dependencies.
- For best performance, ensure Ollama is using your GPU.
- The system is optimized for local, single-user or small-team use.

---
