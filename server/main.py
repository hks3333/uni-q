import os
import logging
import threading
import asyncio
import aiohttp
import httpx
import shutil
import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Import our modular components
from .models import FileLists
from .config import *
from .utils import *
from .research_agent import ResearchAgent
from .routes.research import router as research_router
from .routes.auth import router as auth_router
from .database import init_database
from .auth import verify_token

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

# Token cache for performance optimization
token_cache = {}
TOKEN_CACHE_TTL = 300  # 5 minutes

# Create prompt template
prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=SYSTEM_PROMPT
)

@app.on_event("startup")
async def load_models():
    """Initialize models and services on startup"""
    # Initialize database
    init_database()
    
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
        connector=aiohttp.TCPConnector(limit=20, limit_per_host=10, keepalive_timeout=60)
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

# Include routes
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(research_router, prefix="/research", tags=["research"])

async def get_relevant_documents_async(question, vectorstore):
    """Async wrapper for document retrieval"""
    loop = asyncio.get_event_loop()
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})
    docs = await loop.run_in_executor(None, retriever.invoke, question)
    return docs

async def get_current_student(request: Request):
    """Get current student from request with token caching"""
    auth_header = request.headers.get("Authorization")
    print(f"Auth header received: {auth_header}")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        print("No auth header or invalid format")
        return None
    
    token = auth_header.split(" ")[1]
    print(f"Token extracted: {token[:20]}...")
    
    # Check token cache first
    import time
    current_time = time.time()
    if token in token_cache:
        cached_data = token_cache[token]
        if current_time - cached_data['timestamp'] < TOKEN_CACHE_TTL:
            print("Token found in cache")
            return cached_data['payload']
        else:
            # Remove expired token
            del token_cache[token]
    
    # Verify token
    result = verify_token(token)
    print(f"Token verification result: {result is not None}")
    
    # Cache the result if valid
    if result:
        token_cache[token] = {
            'payload': result,
            'timestamp': current_time
        }
        
        # Clean up old cache entries (keep only last 100)
        if len(token_cache) > 100:
            # Remove oldest entries
            sorted_tokens = sorted(token_cache.items(), key=lambda x: x[1]['timestamp'])
            for old_token, _ in sorted_tokens[:-100]:
                del token_cache[old_token]
    
    return result

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

async def stream_llm_response_with_context(question, embeddings, llm, vectorstore, student_context):
    """Stream LLM response with student context"""
    try:
        # Get relevant documents with context filtering
        docs = await get_relevant_documents_with_context(question, vectorstore, student_context)
        
        # Create context from retrieved documents and track sources
        context_parts = []
        sources = []
        
        for doc in docs:
            context_parts.append(doc.page_content)
            # Extract source information
            source_info = {
                "filename": doc.metadata.get("file_name", "Unknown") + ".pdf",  # Add .pdf extension
                "page": doc.metadata.get("page", 0),
                "title": doc.metadata.get("file_name", "Unknown"),  # Use file_name as title
                "departments": doc.metadata.get("departments", ""),
                "semesters": doc.metadata.get("semesters", "")
            }
            sources.append(source_info)
            # Debug: print available metadata
            print(f"Document metadata: {doc.metadata}")
            print(f"Extracted source: {source_info}")
        
        context = "\n\n".join(context_parts)
        
        # Use centralized context-aware prompt
        full_prompt = CONTEXT_AWARE_PROMPT.format(
            name=student_context['name'],
            roll_no=student_context['roll_no'],
            department=student_context['department'],
            branch=student_context['branch'],
            semester=student_context['semester'],
            context=context,
            question=question
        )
        
        # Stream from Ollama
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
                            # Add source information at the end
                            if sources:
                                yield "\n\n**Sources:**\n"
                                seen_files = set()
                                for i, source in enumerate(sources, 1):
                                    filename = source['filename']
                                    if filename not in seen_files:
                                        seen_files.add(filename)
                                        pdf_url = f"/documents/{filename}"
                                        # Extract just the filename without extension for display
                                        display_name = filename.replace('.pdf', '')
                                        yield f"{i}. [{display_name}]({pdf_url})\n"
                            break
                    except json.JSONDecodeError:
                        continue
                        
    except Exception as e:
        yield f"Error: {str(e)}"

async def stream_general_response(question, student_context):
    """Stream general response without RAG"""
    try:
        # Use centralized general response prompt
        general_prompt = GENERAL_RESPONSE_PROMPT.format(
            name=student_context['name'],
            department=student_context['department'],
            semester=student_context['semester'],
            question=question
        )
        
        # Stream from Ollama
        ollama_url = "http://localhost:11434/api/generate"
        payload = {
            "model": MODEL_NAME,
            "prompt": general_prompt,
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

async def get_relevant_documents_with_context(question, vectorstore, student_context):
    """Get relevant documents filtered by student context"""
    # Get more documents initially
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 10})
    all_docs = await retriever.ainvoke(question)
    
    # Filter documents based on student context
    filtered_docs = filter_documents_by_context(all_docs, student_context)
    
    # Return top 3 filtered documents
    return filtered_docs[:3]

def filter_documents_by_context(docs, student_context):
    """Filter documents based on student's department and semester"""
    filtered = []
    
    for doc in docs:
        metadata = doc.metadata
        relevance_score = 0
        
        # Check department match
        if 'departments' in metadata:
            doc_departments = metadata['departments']
            if isinstance(doc_departments, str):
                doc_departments = doc_departments.split(',')
            
            if student_context['department'] in doc_departments:
                relevance_score += 3
        
        # Check semester match
        if 'semesters' in metadata:
            doc_semesters = metadata['semesters']
            if isinstance(doc_semesters, str):
                doc_semesters = doc_semesters.split(',')
            
            if student_context['semester'] in doc_semesters:
                relevance_score += 2
        
        # Add document with score
        filtered.append((doc, relevance_score))
    
    # Sort by relevance score and return documents
    filtered.sort(key=lambda x: x[1], reverse=True)
    return [doc for doc, score in filtered]

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
    """Stream chat response with document context or general knowledge"""
    data = await request.json()
    question = data.get("question")
    
    if not question:
        return JSONResponse({"error": "No question provided."}, status_code=400)
    
    # Get current student
    current_student = await get_current_student(request)
    if not current_student:
        return JSONResponse({"error": "Authentication required."}, status_code=401)
    
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
        
        # --- Direct Classification (no HTTP overhead) ---
        classification = await classify_query_direct(question, current_student)
        
        # --- Route to appropriate response ---
        if classification == "GENERAL":
            return StreamingResponse(
                stream_general_response(question, current_student),
                media_type="text/plain"
            )
        else:
            return StreamingResponse(
                stream_llm_response_with_context(question, embeddings, llm, vectorstore, current_student),
                media_type="text/plain"
            )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

async def classify_query_direct(question: str, student_context: dict) -> str:
    """Direct classification without HTTP overhead"""
    return await classify_query_shared(question, student_context, app.state.ollama_session)

@app.get("/documents/{filename}")
async def serve_pdf(filename: str):
    """Serve PDF files from the documents directory"""
    try:
        pdf_path = os.path.join(DOCUMENTS_DIR, filename)
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=404, detail="PDF not found")
        
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=filename,
            headers={"Content-Disposition": f"inline; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving PDF: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 