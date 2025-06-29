import os
import csv
import hashlib
import pickle
import numpy as np
import re
from urllib.parse import urlparse
from typing import List
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

def compute_file_hash(files: List[str]) -> str:
    """Compute hash for file list"""
    return hashlib.md5("".join(sorted(files)).encode()).hexdigest()

def load_cached_embeddings(file_hash: str, embed_cache_path: str):
    """Load cached embeddings if available"""
    cache_file = os.path.join(embed_cache_path, f"{file_hash}.pkl")
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            return pickle.load(f)
    return None

def save_cached_embeddings(file_hash: str, documents: List, embeddings: np.ndarray, embed_cache_path: str):
    """Save embeddings to cache"""
    os.makedirs(embed_cache_path, exist_ok=True)
    cache_file = os.path.join(embed_cache_path, f"{file_hash}.pkl")
    with open(cache_file, 'wb') as f:
        pickle.dump({'documents': documents, 'embeddings': embeddings}, f)

def read_metadata_csv(metadata_path: str) -> dict:
    """Read metadata from CSV file"""
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

def delete_file_and_metadata(file_name: str, documents_dir: str):
    """Delete PDF file and its metadata CSV"""
    pdf_path = os.path.join(documents_dir, file_name)
    metadata_path = os.path.join(documents_dir, file_name.replace('.pdf', '.csv'))
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
    if os.path.exists(metadata_path):
        os.remove(metadata_path)

def remove_vectors_from_index(vector_store, file_name: str):
    """Remove vectors for a specific file from the index"""
    vector_store.delete([doc_id for doc_id, doc in vector_store.docstore._dict.items()
                        if doc.metadata.get("file_name") == file_name.replace('.pdf', '')])

def clean_web_content(html_content: str, max_length: int = 8000) -> str:
    """Clean and extract text content from HTML with configurable length limit"""
    if not html_content:
        return ""
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()
        
        # Get text and clean it
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Limit content length (default 8000 chars for research, can be overridden)
        return text[:max_length]
    except Exception as e:
        logger.warning(f"Error cleaning content: {e}")
        return html_content[:max_length] if html_content else ""

def calculate_relevance_score(query: str, content: str) -> float:
    """Calculate relevance score between query and content"""
    if not content or not query:
        return 0.0
    
    query_words = set(query.lower().split())
    content_words = set(content.lower().split())
    
    if not query_words:
        return 0.0
    
    intersection = query_words.intersection(content_words)
    return len(intersection) / len(query_words)

def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except:
        return url 