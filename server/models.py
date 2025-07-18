from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class StudentLogin(BaseModel):
    roll_no: str
    password: str

class StudentRegister(BaseModel):
    roll_no: str
    name: str
    department: str
    branch: str
    semester: str

class StudentResponse(BaseModel):
    id: int
    roll_no: str
    name: str
    department: str
    branch: str
    semester: str

class FileLists(BaseModel):
    new_files: List[str]
    updated_files: List[str]
    deleted_files: List[str]

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
    content: str
    url: str
    source_type: str 