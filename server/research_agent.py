import json
import logging
import asyncio
import re
from typing import List, Dict, Any
from tavily import TavilyClient
from .models import WebSearchResult
from .config import (
    TAVILY_API_KEY, MAX_SEARCH_RESULTS, RESEARCH_PLAN_PROMPT, RESEARCH_SYNTHESIS_PROMPT,
    RESEARCH_PLAN_CONTEXT_SIZE, RESEARCH_CONTEXT_SIZE, RESEARCH_PLAN_TEMPERATURE, 
    RESEARCH_SYNTHESIS_TEMPERATURE, GPU_LAYERS, MODEL_NAME
)
from .utils import clean_web_content, calculate_relevance_score, extract_domain

logger = logging.getLogger(__name__)

class ResearchAgent:
    def __init__(self, ollama_session):
        self.ollama_session = ollama_session
        self.tavily_client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None

    async def search_web_async(self, query: str, max_results: int = None) -> List[WebSearchResult]:
        """Search web using Tavily API"""
        if not self.tavily_client:
            raise Exception("Tavily API key not configured")
        
        max_results = max_results or MAX_SEARCH_RESULTS
        
        try:
            response = self.tavily_client.search(
                query=query,
                search_depth="advanced",
                max_results=max_results,
                include_answer=True,
                include_raw_content=True
            )
            
            results = []
            for result in response.get('results', []):
                # Use larger content limit for research synthesis
                content = clean_web_content(result.get('content', ''), max_length=8000)
                relevance_score = calculate_relevance_score(query, content)
                
                if relevance_score > 0.1:  # Filter low relevance results
                    results.append(WebSearchResult(
                        title=result.get('title', ''),
                        url=result.get('url', ''),
                        content=content,
                        relevance_score=relevance_score,
                        source_type=extract_domain(result.get('url', ''))
                    ))
            
            # Sort by relevance score
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"Error in web search: {e}")
            raise Exception(f"Web search failed: {str(e)}")

    async def generate_research_plan(self, query: str) -> Dict[str, Any]:
        """Generate research plan using Llama3.2 with optimized settings"""
        try:
            prompt = RESEARCH_PLAN_PROMPT.format(query=query)
            
            # Use Ollama directly for plan generation with research-optimized settings
            ollama_url = "http://localhost:11434/api/generate"
            payload = {
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": RESEARCH_PLAN_TEMPERATURE,
                    "num_ctx": RESEARCH_PLAN_CONTEXT_SIZE,
                    "num_gpu": GPU_LAYERS
                }
            }
            
            async with self.ollama_session.post(ollama_url, json=payload) as response:
                if response.status != 200:
                    raise Exception(f"Ollama API error: {response.status}")
                
                data = await response.json()
                response_text = data.get('response', '')
                
                # Try to parse JSON from response
                try:
                    # Find JSON in the response
                    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                    if json_match:
                        plan = json.loads(json_match.group())
                    else:
                        # Fallback: create a detailed plan
                        plan = {
                            "objectives": [
                                f"Research {query} comprehensively",
                                f"Find latest developments and research in {query}",
                                f"Identify key experts and authoritative sources on {query}"
                            ],
                            "search_queries": [
                                f"{query} latest research papers 2024",
                                f"{query} recent developments news",
                                f"{query} expert analysis insights",
                                f"{query} technical documentation guide"
                            ],
                            "sources": [
                                "academic papers and research journals",
                                "latest news and industry reports", 
                                "expert opinions and analysis",
                                "technical documentation and guides"
                            ],
                            "analysis_framework": [
                                "background and fundamentals",
                                "current state and latest developments",
                                "key findings and breakthroughs",
                                "implications and future outlook"
                            ]
                        }
                    
                    return plan
                    
                except json.JSONDecodeError:
                    # Fallback plan if JSON parsing fails
                    return {
                        "objectives": [
                            f"Research {query} comprehensively",
                            f"Find latest developments and research in {query}",
                            f"Identify key experts and authoritative sources on {query}"
                        ],
                        "search_queries": [
                            f"{query} latest research papers 2024",
                            f"{query} recent developments news",
                            f"{query} expert analysis insights",
                            f"{query} technical documentation guide"
                        ],
                        "sources": [
                            "academic papers and research journals",
                            "latest news and industry reports", 
                            "expert opinions and analysis",
                            "technical documentation and guides"
                        ],
                        "analysis_framework": [
                            "background and fundamentals",
                            "current state and latest developments",
                            "key findings and breakthroughs",
                            "implications and future outlook"
                        ]
                    }
                    
        except Exception as e:
            logger.error(f"Error generating research plan: {e}")
            raise Exception(f"Failed to generate research plan: {str(e)}")

    async def synthesize_research_results(self, query: str, plan: Dict[str, Any], search_results: List[WebSearchResult]) -> str:
        """Synthesize research results using Llama3.2 with large context window"""
        try:
            # Prepare content from search results
            content_parts = []
            for i, result in enumerate(search_results, 1):
                content_parts.append(f"Source {i} ({result.source_type}):\n{result.content}\nURL: {result.url}\n")
            
            content = "\n".join(content_parts)
            
            # Create synthesis prompt
            synthesis_prompt = RESEARCH_SYNTHESIS_PROMPT.format(
                query=query,
                plan=json.dumps(plan, indent=2),
                content=content
            )
            
            # Use Ollama for synthesis with large context window
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
            
            async with self.ollama_session.post(ollama_url, json=payload) as response:
                if response.status != 200:
                    raise Exception(f"Ollama API error: {response.status}")
                
                full_response = ""
                async for line in response.content:
                    if line:
                        try:
                            data = json.loads(line.decode('utf-8'))
                            if 'response' in data:
                                full_response += data['response']
                            if data.get('done', False):
                                break
                        except json.JSONDecodeError:
                            continue
                
                return full_response
                
        except Exception as e:
            logger.error(f"Error synthesizing research results: {e}")
            raise Exception(f"Failed to synthesize research results: {str(e)}")

    async def execute_research_plan(self, query: str, plan: Dict[str, Any]) -> List[WebSearchResult]:
        """Execute a research plan and return search results"""
        try:
            # Get search queries from plan
            search_queries = plan.get('search_queries', [query])
            
            # Perform web searches
            all_results = []
            for query in search_queries[:4]:  # Limit to 4 queries
                try:
                    results = await self.search_web_async(query, MAX_SEARCH_RESULTS)
                    all_results.extend(results)
                except Exception as e:
                    logger.warning(f"Search failed for query '{query}': {e}")
                    continue
            
            # Remove duplicates and sort by relevance
            unique_results = {}
            for result in all_results:
                if result.url not in unique_results:
                    unique_results[result.url] = result
            
            sorted_results = sorted(unique_results.values(), key=lambda x: x.relevance_score, reverse=True)
            
            return sorted_results[:MAX_SEARCH_RESULTS]
            
        except Exception as e:
            logger.error(f"Error executing research plan: {e}")
            raise Exception(f"Failed to execute research plan: {str(e)}") 