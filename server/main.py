import os
import logging
import threading
import asyncio
import aiohttp
import tempfile
import shutil
import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

# Import our modular components
from .models import FileLists
from .config import *
from .utils import *
from .research_agent import ResearchAgent
from .routes.research import router as research_router

# Import LangChain components
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate

# Initialize FastAPI app
app = FastAPI(title="Knowledge Base Ingestion Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    filename="ingestion_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create prompt template
prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=SYSTEM_PROMPT
)

@app.on_event("startup")
async def load_models():
    """Initialize models and services on startup"""
    try:
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        device = "cpu"
    
    # Initialize embeddings
    app.state.embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": device, "trust_remote_code": False},
        encode_kwargs={"normalize_embeddings": True, "batch_size": BATCH_SIZE}
    )
    
    # Initialize LLM with optimized settings for chat
    app.state.llm = OllamaLLM(
        model=MODEL_NAME,
        temperature=CHAT_TEMPERATURE,
        num_ctx=CHAT_CONTEXT_SIZE,
        num_gpu=GPU_LAYERS,
        timeout=600
    )
    
    # Create connection pool for Ollama
    app.state.ollama_session = aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=600),
        connector=aiohttp.TCPConnector(limit=10, limit_per_host=5)
    )
    
    # Initialize research agent
    app.state.research_agent = ResearchAgent(app.state.ollama_session)
    
    # Preload FAISS index if it exists
    if os.path.exists(FAISS_INDEX_PATH):
        app.state.vectorstore = FAISS.load_local(FAISS_INDEX_PATH, app.state.embeddings, allow_dangerous_deserialization=True)
    else:
        app.state.vectorstore = None
    
    app.state.vectorstore_lock = threading.Lock()

@app.on_event("shutdown")
async def cleanup():
    """Cleanup resources on shutdown"""
    if hasattr(app.state, 'ollama_session'):
        await app.state.ollama_session.close()

# Include research routes
app.include_router(research_router, prefix="/research", tags=["research"])

async def get_relevant_documents_async(question, vectorstore):
    """Async wrapper for document retrieval"""
    loop = asyncio.get_event_loop()
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})
    docs = await loop.run_in_executor(None, retriever.invoke, question)
    return docs

async def stream_llm_response(question, embeddings, llm, vectorstore):
    """Stream LLM response for chat"""
    try:
        # Start document retrieval asynchronously
        retrieval_task = asyncio.create_task(
            get_relevant_documents_async(question, vectorstore)
        )
        
        # Wait for retrieval to complete
        docs = await retrieval_task
        
        # Create context from retrieved documents
        context = "\n\n".join([doc.page_content for doc in docs])
        
        # Use the proper SYSTEM_PROMPT template
        full_prompt = prompt.format(context=context, question=question)
        
        # Stream from Ollama using connection pool with chat-optimized settings
        ollama_url = "http://localhost:11434/api/generate"
        payload = {
            "model": MODEL_NAME,
            "prompt": full_prompt,
            "stream": True,
            "options": {
                "temperature": CHAT_TEMPERATURE,
                "num_ctx": CHAT_CONTEXT_SIZE,
                "num_gpu": GPU_LAYERS
            }
        }
        
        async with app.state.ollama_session.post(ollama_url, json=payload) as response:
            async for line in response.content:
                if line:
                    try:
                        data = json.loads(line.decode('utf-8'))
                        if 'response' in data:
                            yield data['response']
                        if data.get('done', False):
                            break
                    except json.JSONDecodeError:
                        continue
                        
    except Exception as e:
        yield f"Error: {str(e)}"

def embed_documents_optimized(documents, embeddings_model, file_hash):
    """Optimized document embedding with caching"""
    cached = load_cached_embeddings(file_hash, EMBED_CACHE_PATH)
    if cached:
        logger.info(f"Loaded {len(cached['documents'])} cached embeddings")
        return cached['documents'], cached['embeddings']
    
    texts = [doc.page_content for doc in documents if len(doc.page_content.strip()) > 50]
    documents = [doc for doc in documents if len(doc.page_content.strip()) > 50]
    logger.info(f"Embedding {len(texts)} chunks (filtered from original)...")
    
    embeddings_array = []
    batch_size = 8
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        batch_embeddings = embeddings_model.embed_documents(batch)
        embeddings_array.extend(batch_embeddings)
    
    save_cached_embeddings(file_hash, documents, embeddings_array, EMBED_CACHE_PATH)
    return documents, embeddings_array

def process_pdf_optimized(file_path: str):
    """Process PDF file and split into chunks"""
    loader = PyMuPDFLoader(file_path)
    pages = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    return text_splitter.split_documents(pages)

@app.post("/update_knowledge_base")
async def update_knowledge_base(file_lists: FileLists):
    """Update the knowledge base with new, updated, or deleted files"""
    try:
        logger.info("Starting knowledge base update")
        logger.info(f"New files: {file_lists.new_files}")
        logger.info(f"Updated files: {file_lists.updated_files}")
        logger.info(f"Deleted files: {file_lists.deleted_files}")

        # Process deleted files
        for file in file_lists.deleted_files:
            logger.info(f"Removing vectors and files for {file}")
            with app.state.vectorstore_lock:
                vectorstore = app.state.vectorstore
                if vectorstore:
                    remove_vectors_from_index(vectorstore, file)
            delete_file_and_metadata(file, DOCUMENTS_DIR)

        # Process new and updated files
        all_documents = []
        all_files = file_lists.new_files + file_lists.updated_files
        temp_files = []
        
        for file in all_files:
            pdf_path = os.path.join(DOCUMENTS_DIR, file)
            metadata_path = os.path.join(DOCUMENTS_DIR, file.replace('.pdf', '.csv'))
            
            if not os.path.exists(pdf_path) or not os.path.exists(metadata_path):
                logger.warning(f"File or metadata missing: {file}")
                continue
                
            metadata = read_metadata_csv(metadata_path)
            documents = process_pdf_optimized(pdf_path)
            
            for doc in documents:
                doc.metadata.update(metadata)
            
            all_documents.extend(documents)
            temp_files.append(file)

        # Update FAISS index
        if all_documents:
            file_hash = compute_file_hash(temp_files)
            documents, embedding_vectors = embed_documents_optimized(all_documents, app.state.embeddings, file_hash)
            text_embeddings = list(zip([doc.page_content for doc in documents], embedding_vectors))
            
            with app.state.vectorstore_lock:
                vectorstore = app.state.vectorstore
                if vectorstore is None:
                    vectorstore = FAISS.from_embeddings(
                        text_embeddings,
                        app.state.embeddings,
                        metadatas=[doc.metadata for doc in documents]
                    )
                else:
                    vectorstore.add_embeddings(
                        text_embeddings,
                        metadatas=[doc.metadata for doc in documents]
                    )
            
            # Save updated FAISS index locally
            if vectorstore:
                if os.path.exists(FAISS_INDEX_PATH):
                    shutil.rmtree(FAISS_INDEX_PATH)
                vectorstore.save_local(FAISS_INDEX_PATH)
                logger.info(f"Saved updated FAISS index to {FAISS_INDEX_PATH}")

        logger.info("Knowledge base update completed successfully")
        return {"message": "Knowledge base updated successfully"}

    except Exception as e:
        logger.error(f"Error updating knowledge base: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating knowledge base: {e}")

@app.post("/chat/stream")
async def chat_stream(request: Request):
    """Stream chat response with document context"""
    data = await request.json()
    question = data.get("question")
    
    if not question:
        return JSONResponse({"error": "No question provided."}, status_code=400)
    
    try:
        embeddings = app.state.embeddings
        llm = app.state.llm
        
        with app.state.vectorstore_lock:
            vectorstore = app.state.vectorstore
            if vectorstore is None and os.path.exists(FAISS_INDEX_PATH):
                vectorstore = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
                app.state.vectorstore = vectorstore
        
        if vectorstore is None:
            return JSONResponse({"error": "Knowledge base is not built yet."}, status_code=500)
        
        return StreamingResponse(
            stream_llm_response(question, embeddings, llm, vectorstore),
            media_type="text/plain"
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 