from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
import json
import logging
import aiohttp
from typing import Dict, Any, List

from ..models import ResearchPlanRequest, ResearchPlanResponse, ResearchExecuteRequest, ResearchExecuteResponse, WebSearchResult
from ..config import (
    RESEARCH_MODE_ENABLED, RESEARCH_SYNTHESIS_PROMPT, RESEARCH_CONTEXT_SIZE, 
    RESEARCH_SYNTHESIS_TEMPERATURE, GPU_LAYERS, MODEL_NAME
)
from ..research_agent import ResearchAgent

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_research_agent():
    """Create a ResearchAgent instance with aiohttp session"""
    session = aiohttp.ClientSession()
    return ResearchAgent(session)

async def stream_research_response(query: str, plan: Dict[str, Any], search_results: List[Dict[str, Any]]):
    """Stream research synthesis response with optimized context window"""
    try:
        research_agent = await get_research_agent()
        
        # Convert search results back to WebSearchResult objects
        web_results = [WebSearchResult(**result) for result in search_results]
        
        # Prepare content from search results
        content_parts = []
        for i, result in enumerate(web_results, 1):
            content_parts.append(f"Source {i} ({result.source_type}):\n{result.content}\nURL: {result.url}\n")
        
        content = "\n".join(content_parts)
        
        # Create synthesis prompt
        synthesis_prompt = RESEARCH_SYNTHESIS_PROMPT.format(
            query=query,
            plan=json.dumps(plan, indent=2),
            content=content
        )
        
        # Stream from Ollama with large context window for research synthesis
        ollama_url = "http://localhost:11434/api/generate"
        payload = {
            "model": MODEL_NAME,
            "prompt": synthesis_prompt,
            "stream": True,
            "options": {
                "temperature": RESEARCH_SYNTHESIS_TEMPERATURE,
                "num_ctx": RESEARCH_CONTEXT_SIZE,  # 24K context for research synthesis
                "num_gpu": GPU_LAYERS
            }
        }
        
        async with research_agent.ollama_session.post(ollama_url, json=payload) as response:
            if response.status != 200:
                yield f"Error: Ollama API error {response.status}"
                return
            
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

@router.post("/plan")
async def create_research_plan(request: ResearchPlanRequest):
    """Generate a research plan for the given query"""
    if not RESEARCH_MODE_ENABLED:
        return JSONResponse({"error": "Research mode is disabled"}, status_code=400)
    
    try:
        research_agent = await get_research_agent()
        plan = await research_agent.generate_research_plan(request.query)
        
        # Debug logging
        logger.info(f"Generated plan type: {type(plan)}")
        logger.info(f"Generated plan: {plan}")
        
        # Ensure plan has required fields
        if not isinstance(plan, dict):
            logger.error(f"Plan is not a dict: {type(plan)}")
            plan = {
                "objectives": [f"Research {request.query} comprehensively"],
                "search_queries": [f"{request.query} latest research 2024"],
                "sources": ["academic papers", "news articles", "expert analysis"],
                "analysis_framework": ["background", "current state", "future outlook"]
            }
        
        # Ensure all required fields are arrays
        for field in ["objectives", "search_queries", "sources", "analysis_framework"]:
            if field not in plan or not isinstance(plan[field], list):
                logger.warning(f"Plan missing or invalid field '{field}': {plan.get(field)}")
                plan[field] = []
        
        return ResearchPlanResponse(
            plan=plan,
            query=request.query,
            status="success"
        )
    except Exception as e:
        logger.error(f"Error creating research plan: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@router.post("/execute")
async def execute_research_plan(request: ResearchExecuteRequest):
    """Execute a research plan and return results"""
    if not RESEARCH_MODE_ENABLED:
        return JSONResponse({"error": "Research mode is disabled"}, status_code=400)
    
    try:
        research_agent = await get_research_agent()
        
        # Use refined plan if provided, otherwise use original plan
        plan = request.refined_plan if request.refined_plan else request.plan
        
        # Execute the research plan
        search_results = await research_agent.execute_research_plan(request.query, plan)
        
        return ResearchExecuteResponse(
            query=request.query,
            plan=plan,
            sources=[result.dict() for result in search_results],
            status="success"
        )
    except Exception as e:
        logger.error(f"Error executing research plan: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@router.post("/stream")
async def research_stream(request: Request):
    """Stream research synthesis response"""
    if not RESEARCH_MODE_ENABLED:
        return JSONResponse({"error": "Research mode is disabled"}, status_code=400)
    
    data = await request.json()
    query = data.get("query")
    plan = data.get("plan")
    search_results = data.get("search_results", [])
    
    if not query or not plan:
        return JSONResponse({"error": "Query and plan are required"}, status_code=400)
    
    try:
        return StreamingResponse(
            stream_research_response(query, plan, search_results),
            media_type="text/plain"
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500) 