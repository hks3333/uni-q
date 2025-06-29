from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# File Management Models
class FileLists(BaseModel):
    new_files: List[str]
    updated_files: List[str]
    deleted_files: List[str]

# Research Agent Models
class ResearchPlanRequest(BaseModel):
    query: str

class ResearchPlanResponse(BaseModel):
    plan: Dict[str, Any]
    query: str
    status: str

class ResearchExecuteRequest(BaseModel):
    query: str
    plan: Dict[str, Any]
    refined_plan: Optional[Dict[str, Any]] = None

class ResearchExecuteResponse(BaseModel):
    query: str
    plan: Dict[str, Any]
    sources: List[Dict[str, Any]]
    status: str

class WebSearchResult(BaseModel):
    title: str
    url: str
    content: str
    relevance_score: float
    source_type: str 