import os
import csv
import logging
from io import StringIO
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from typing import List
import tempfile
import pickle
import hashlib
import numpy as np
import shutil
from langchain_ollama import OllamaLLM
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import threading

# Always use the parent directory's documents folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCUMENTS_DIR = os.path.join(BASE_DIR, "documents")
FAISS_INDEX_PATH = "faiss_index"
EMBED_CACHE_PATH = "embed_cache"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 128
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
BATCH_SIZE = 16
MODEL_NAME = "phi3.5:3.8b"
SYSTEM_PROMPT = """
You are Uni-Q, an expert, friendly assistant for university students and faculty. Your job is to answer questions 
as clearly, concisely, and technically accurately as possible. Use the information provided in the 
context below to answer, and if you are very confident and it's natural, you may gently generalize 
from your own knowledge—but always prefer the context if it is relevant. Select the most appropriate 
information from the context to answer the user's question, and do not mention the context or 
documents in your response. If you truly don't know the answer, it's okay to admit it in a professional, 
lightly humorous way (for example, "I wish I knew!" or "That one's above my pay grade!"). 
Never make up facts if you are unsure. Keep your tone knowledgeable, approachable, and only add a subtle 
touch of humor when appropriate.

Context:
{context}

Question:
{question}

Answer:
"""
prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=SYSTEM_PROMPT
)

# Initialize FastAPI app
app = FastAPI(title="Knowledge Base Ingestion Server")

# Configure logging
logging.basicConfig(
    filename="ingestion_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Pydantic model for request body
class FileLists(BaseModel):
    new_files: List[str]
    updated_files: List[str]
    deleted_files: List[str]

def compute_file_hash(files: List[str]) -> str:
    return hashlib.md5("".join(sorted(files)).encode()).hexdigest()

def load_cached_embeddings(file_hash: str):
    cache_file = os.path.join(EMBED_CACHE_PATH, f"{file_hash}.pkl")
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            return pickle.load(f)
    return None

def save_cached_embeddings(file_hash: str, documents: List, embeddings: np.ndarray):
    os.makedirs(EMBED_CACHE_PATH, exist_ok=True)
    cache_file = os.path.join(EMBED_CACHE_PATH, f"{file_hash}.pkl")
    with open(cache_file, 'wb') as f:
        pickle.dump({'documents': documents, 'embeddings': embeddings}, f)

def embed_documents_optimized(documents: List, embeddings_model, file_hash: str):
    cached = load_cached_embeddings(file_hash)
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
    save_cached_embeddings(file_hash, documents, embeddings_array)
    return documents, embeddings_array

def process_pdf_optimized(file_path: str) -> List:
    loader = PyMuPDFLoader(file_path)
    pages = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    return text_splitter.split_documents(pages)

def read_metadata_csv(metadata_path: str) -> dict:
    with open(metadata_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        file_name, departments, semesters, tags = next(reader)
        return {
            "file_name": file_name,
            "departments": departments.split(","),
            "semesters": semesters.split(","),
            "tags": tags.split(",")
        }

def delete_file_and_metadata(file_name: str):
    pdf_path = os.path.join(DOCUMENTS_DIR, file_name)
    metadata_path = os.path.join(DOCUMENTS_DIR, file_name.replace('.pdf', '.csv'))
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
    if os.path.exists(metadata_path):
        os.remove(metadata_path)

def remove_vectors_from_index(vector_store, file_name: str):
    # Remove vectors where metadata["file_name"] matches
    vector_store.delete([doc_id for doc_id, doc in vector_store.docstore._dict.items()
                        if doc.metadata.get("file_name") == file_name.replace('.pdf', '')])

@app.on_event("startup")
def load_models():
    try:
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        device = "cpu"
    app.state.embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": device, "trust_remote_code": False},
        encode_kwargs={"normalize_embeddings": True, "batch_size": BATCH_SIZE}
    )
    app.state.llm = OllamaLLM(
        model=MODEL_NAME,
        temperature=0.4,
        num_ctx=4096,
        num_gpu=50,
        timeout=600
    )
    # Preload FAISS index if it exists
    if os.path.exists(FAISS_INDEX_PATH):
        app.state.vectorstore = FAISS.load_local(FAISS_INDEX_PATH, app.state.embeddings, allow_dangerous_deserialization=True)
    else:
        app.state.vectorstore = None
    app.state.vectorstore_lock = threading.Lock()

@app.post("/update_knowledge_base")
async def update_knowledge_base(file_lists: FileLists):
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
            delete_file_and_metadata(file)

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

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    question = data.get("question")
    if not question:
        return JSONResponse({"error": "No question provided."}, status_code=400)
    try:
        # Use preloaded models
        embeddings = app.state.embeddings
        llm = app.state.llm
        with app.state.vectorstore_lock:
            vectorstore = app.state.vectorstore
            # Reload if index was rebuilt
            if vectorstore is None and os.path.exists(FAISS_INDEX_PATH):
                vectorstore = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
                app.state.vectorstore = vectorstore
        if vectorstore is None:
            return JSONResponse({"error": "Knowledge base is not built yet."}, status_code=500)
        retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})
        qa = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt}
        )
        result = qa.invoke(question)
        answer = result["result"]
        sources = result.get("source_documents", [])
        # Collect unique file names from sources
        file_names = set()
        for doc in sources:
            file_name = doc.metadata.get("file_name")
            if file_name:
                file_names.add(file_name + ".pdf" if not file_name.endswith(".pdf") else file_name)
        sources_list = [{"file_name": fn} for fn in sorted(file_names)]
        return {"answer": answer, "sources": sources_list}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)