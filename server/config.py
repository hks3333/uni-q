import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCUMENTS_DIR = os.path.join(BASE_DIR, "documents")
FAISS_INDEX_PATH = "faiss_index"
EMBED_CACHE_PATH = "embed_cache"

# Document Processing
CHUNK_SIZE = 512
CHUNK_OVERLAP = 128
BATCH_SIZE = 16

# Models
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
MODEL_NAME = "llama3.2:latest"

# Research Agent Configuration
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
RESEARCH_MODE_ENABLED = os.getenv("RESEARCH_MODE_ENABLED", "true").lower() == "true"
MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", "5"))
RESEARCH_TIMEOUT = int(os.getenv("RESEARCH_TIMEOUT", "300"))

# Llama3.2 Configuration
# Llama3.2 supports up to 32K context window
CHAT_CONTEXT_SIZE = 8192  # 8K for regular chat (sufficient for document context)
RESEARCH_CONTEXT_SIZE = 24576  # 24K for research synthesis (allows for multiple sources)
RESEARCH_PLAN_CONTEXT_SIZE = 8192  # 8K for plan generation

# Model Parameters
CHAT_TEMPERATURE = 0.4
RESEARCH_PLAN_TEMPERATURE = 0.3
RESEARCH_SYNTHESIS_TEMPERATURE = 0.4
GPU_LAYERS = 50

# Prompts
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

RESEARCH_PLAN_PROMPT = """
You are an expert research assistant. Create a detailed, step-by-step research plan for the following query:

Query: {query}

Generate a comprehensive research plan with specific, actionable steps. Focus on finding the most recent, authoritative, and relevant information.

Your plan MUST include these 4 sections as a JSON object:

1. **objectives**: [list of 3-4 specific research goals]
2. **search_queries**: [list of 4-6 specific search terms for different source types]
3. **sources**: [list of 4-6 specific source types to explore]
4. **analysis_framework**: [list of 4-5 analysis points and structure]

IMPORTANT: The search_queries field MUST contain specific, actionable search terms. Examples:
- For "AI trends 2024": ["artificial intelligence latest research papers 2024", "AI breakthrough news 2024", "machine learning expert analysis current state", "AI industry trends report 2024", "artificial intelligence technical implementation guide", "AI future predictions 2024"]
- For "quantum computing": ["quantum computing latest research papers 2024", "quantum computer breakthrough news 2024", "quantum computing expert analysis current state", "quantum computing industry report 2024", "quantum computing technical implementation guide", "quantum computing future predictions 2024"]

Format your response as a VALID JSON object with these exact field names:
{{
  "objectives": [
    "Research {query} comprehensively",
    "Find latest developments and research in {query}",
    "Identify key experts and authoritative sources on {query}",
    "Analyze current trends and future outlook for {query}"
  ],
  "search_queries": [
    "{query} latest research papers 2024",
    "{query} recent developments news 2024",
    "{query} expert analysis insights",
    "{query} technical documentation guide",
    "{query} industry trends report 2024",
    "{query} future predictions 2024"
  ],
  "sources": [
    "academic papers and research journals",
    "latest news and industry reports",
    "expert opinions and analysis",
    "technical documentation and guides",
    "industry reports and market analysis",
    "government and institutional reports"
  ],
  "analysis_framework": [
    "background and fundamentals",
    "current state and latest developments",
    "key findings and breakthroughs",
    "implications and future outlook",
    "expert consensus and predictions"
  ]
}}

Make each search query specific and targeted. DO NOT leave any field empty. Ensure the JSON is valid and complete.
"""

RESEARCH_SYNTHESIS_PROMPT = """
Based on the research plan and gathered information, provide a comprehensive, well-structured analysis:

Original Query: {query}
Research Plan: {plan}
Gathered Information: {content}

Provide a detailed, structured response that:

1. **Directly addresses the original query** with clear, comprehensive answers
2. **Follows the research plan structure** and objectives
3. **Synthesizes information from multiple sources** with proper attribution
4. **Presents findings in a clear, organized manner** with:
   - Executive summary of key findings
   - Detailed analysis organized by themes/topics
   - Clear conclusions and implications
   - Proper source citations
5. **Maintains academic rigor** while being accessible and engaging
6. **Highlights conflicting information** and provides balanced perspectives

Structure your response with clear sections, bullet points for key findings, and include source links where relevant. Make the content easy to read and understand.
""" 