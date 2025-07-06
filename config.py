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
You are Uni-Q, an expert, friendly assistant for university students and faculty. Your primary responsibility 
is to answer questions based on the information provided in the context below. 

**IMPORTANT GUIDELINES:**
- Answer questions primarily from the provided context/documents
- Only use your general knowledge to supplement or clarify information from the context, not as the main source
- If the context doesn't contain relevant information to answer the question, clearly state that the information is not available in the provided documents
- Format your responses in markdown for better readability
- Use appropriate markdown formatting (headers, lists, code blocks, emphasis) to structure your answers
- Keep your tone knowledgeable and approachable

**Response Format:**
- Use markdown formatting for structure and readability
- Include relevant details from the context
- If information is missing from the context, acknowledge this clearly
- Do not mention the context or documents in your response

Context:
{context}

Question:
{question}

Answer:
"""

RESEARCH_PLAN_PROMPT = """
You are an expert research assistant specializing in creating highly effective research plans. Your task is to generate a detailed, step-by-step research plan for the given query.

**Your goal is to enable a user to efficiently find the most recent, authoritative, and relevant information on the query.**

**Query:** {query}

---

**Internal Thinking Process (for your own guidance, not part of the output):**
1.  **Deconstruct the Query:** Identify the core subject and implied scope (e.g., industry, specific technology, historical context vs. current trends, global vs. regional).
2.  **Define Objectives:** What are the 3-4 most critical, measurable outcomes of this research? Make them specific to the query.
3.  **Brainstorm Search Terms:**
    * Consider different angles: general overview, recent developments, expert analysis, technical aspects, industry reports, future predictions, specific sub-topics if applicable.
    * Think about keywords that reliable sources would use.
    * Include recent year (e.g., 2024, 2025) if applicable to ensure recency.
    * Vary the terms to capture different search results.
4.  **Identify Source Types:** What categories of information are most likely to contain authoritative data for this query? Think beyond just "news" – consider academic, governmental, corporate, and analytical.
5.  **Develop Analysis Framework:** How will the gathered information be structured and evaluated to answer the query effectively? What are the logical sections of a comprehensive answer?

---

**Output Format (MUST be a VALID JSON object, Example only for guidance.):**
{{
  "objectives": [
    // List 3-4 highly specific research goals tailored to the query.
    // Example for "trends in automation industry": "Identify the top 3-5 emerging technological trends in automation (e.g., AI in robotics, industrial IoT, collaborative robots).", "Assess the current market size and projected growth of the automation industry globally.", "Analyze the impact of automation trends on labor markets and skill requirements."
  ],
  "search_queries": [
    // List 4-6 specific, targeted search terms.
    // Use keywords from the query and derived sub-topics.
    // Incorporate terms for recency (e.g., "2024", "recent", "latest").
    // Vary the type of information sought (e.g., "report", "research", "analysis", "case studies").
    // Example for "trends in automation industry": "automation industry trends 2024-2025 report", "impact of AI on industrial automation", "robotics market growth projections", "future of automation jobs and skills", "emerging automation technologies analysis", "automation industry challenges and opportunities"
  ],
  "sources": [
    // List 4-6 specific source *types* relevant to the query.
    // Be more granular than just "news".
    // Examples: "market research reports (Gartner, IDC)", "academic journals (IEEE, ACM)", "technology news outlets (TechCrunch, Wired)", "industry association publications", "government economic reports", "corporate white papers and blogs of leading companies"
  ],
  "analysis_framework": [
    // List 4-5 key sections or analytical points for structuring the final research output.
    // Example for "trends in automation industry": "Definition and scope of the automation industry", "Key technological trends and their current state", "Market analysis and economic impact (growth, investment)", "Societal implications (employment, ethics)", "Future outlook and strategic recommendations"
  ]
}}

Make sure your response is a perfectly valid JSON object. Ensure all fields are populated with highly relevant and specific content derived directly from the query's implications. DO NOT include any explanatory text outside the JSON.
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

QUERY_CLASSIFICATION_PROMPT = """
Classify this query as GENERAL or RAG:

GENERAL: greetings, casual chat, general knowledge questions, personal questions, jokes, weather, general advice not specific to courses
RAG: questions about specific course content, assignments, syllabus, documents, study materials, exam questions, project requirements, anything that needs document lookup

Examples:
- "hi" → GENERAL
- "how are you" → GENERAL  
- "what is AI" → GENERAL
- "explain chapter 3" → RAG
- "what are the assignment guidelines" → RAG
- "summarize the syllabus" → RAG
- "how does IPO cycle work" → RAG

Student: {department}, {semester}
Query: {query}

Answer with only GENERAL or RAG:
""" 