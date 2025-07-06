# Research Mode - Complete Flow Documentation

## Overview
This document explains the complete flow of what happens when a user sends a query in **research mode**. The system generates an AI research plan, performs web searches, and synthesizes comprehensive research reports.

## User Input → Output Flow

### 1. **Frontend: User Interface (next-frontend/app/page.js)**
- **Component**: `ChatPage` function
- **User Action**: 
  - Toggles "Research Mode" switch to `true`
  - Types research query in chat input and presses Enter
- **Trigger**: `sendMessage()` function is called
- **Decision**: `researchMode` is `true`, so `handleResearchQuery()` is executed

### 2. **Frontend: Research Mode Processing (next-frontend/app/page.js)**
- **Function**: `handleResearchQuery(userMessage)`
- **Actions**:
  - Sets `researchState` to `'planning'`
  - Prepares request payload: `{ query: userMessage }`
  - Calls research plan generation API

### 3. **Frontend API Route: Research Plan Proxy (next-frontend/app/api/research/plan/route.js)**
- **File**: `next-frontend/app/api/research/plan/route.js`
- **Function**: `POST` handler
- **Actions**:
  - Receives research query from frontend
  - Forwards request to FastAPI backend at `http://localhost:8000/research/plan`
  - Returns research plan JSON response

### 4. **Backend: Research Plan Generation (server/routes/research.py)**
- **File**: `server/routes/research.py`
- **Function**: `create_research_plan()`
- **Actions**:
  - Validates research mode is enabled
  - Creates `ResearchAgent` instance with aiohttp session
  - Calls `generate_research_plan()` method

### 5. **Backend: AI Research Plan Creation (server/research_agent.py)**
- **File**: `server/research_agent.py`
- **Function**: `generate_research_plan(query)`
- **Process**:
  - Formats research plan prompt with user query
  - Sends request to Ollama API with research-optimized settings:
    - Model: `llama3.2:latest`
    - Context window: 8K tokens
    - Temperature: 0.3
    - GPU layers: 50
  - Parses JSON response to extract research plan structure
  - Returns structured plan with objectives, search queries, sources, and analysis framework

### 6. **Frontend: Plan Display (next-frontend/app/page.js)**
- **Function**: `handleResearchQuery()` (continued)
- **Actions**:
  - Receives research plan from API
  - Sets `currentPlan` state
  - Adds bot message with plan display
  - Sets `researchState` back to `null`
  - Renders `ResearchPlan` component

### 7. **Frontend: Research Plan Component (next-frontend/components/ResearchPlan.js)**
- **File**: `next-frontend/components/ResearchPlan.js`
- **Component**: `ResearchPlan`
- **Features**:
  - Displays research objectives as bullet points
  - Shows search strategy with numbered steps
  - Lists information sources as tags
  - Presents analysis framework structure
  - Provides "Edit Plan" and "Execute Plan" buttons

### 8. **User Interaction: Plan Refinement (Optional)**
- **User Action**: Clicks "Edit Plan" button
- **Function**: `handleEdit()` in ResearchPlan component
- **Process**:
  - Enables editing mode
  - Allows user to modify plan structure
  - "Save" button calls `handlePlanRefine()` to update plan
  - "Cancel" button reverts to original plan

### 9. **User Action: Execute Research Plan**
- **User Action**: Clicks "Execute Plan" button
- **Function**: `handlePlanExecute(plan)` in page.js
- **Actions**:
  - Sets `researchState` to `'executing'`
  - Prepares request with original query and plan
  - Calls research execution API

### 10. **Frontend API Route: Research Execute Proxy (next-frontend/app/api/research/execute/route.js)**
- **File**: `next-frontend/app/api/research/execute/route.js`
- **Function**: `POST` handler
- **Actions**:
  - Forwards request to FastAPI backend at `http://localhost:8000/research/execute`
  - Returns search results and plan data

### 11. **Backend: Research Plan Execution (server/routes/research.py)**
- **File**: `server/routes/research.py`
- **Function**: `execute_research_plan()`
- **Actions**:
  - Creates `ResearchAgent` instance
  - Calls `execute_research_plan()` method with query and plan

### 12. **Backend: Web Search Execution (server/research_agent.py)**
- **File**: `server/research_agent.py`
- **Function**: `execute_research_plan(query, plan)`
- **Process**:
  - Extracts search queries from plan
  - Iterates through search queries (limited to 4)
  - For each query, calls `search_web_async()`

### 13. **Backend: Tavily Web Search (server/research_agent.py)**
- **File**: `server/research_agent.py`
- **Function**: `search_web_async(query, max_results)`
- **Process**:
  - Uses Tavily API client for web search
  - Performs "advanced" depth search
  - Retrieves up to 5 results per query
  - Includes raw content and metadata
  - Cleans and processes web content (8K character limit)
  - Calculates relevance scores
  - Filters low-relevance results (< 0.1 score)
  - Returns `WebSearchResult` objects

### 14. **Backend: Content Processing (server/utils.py)**
- **File**: `server/utils.py`
- **Functions**:
  - `clean_web_content()` - Removes HTML, normalizes text
  - `calculate_relevance_score()` - Semantic similarity scoring
  - `extract_domain()` - Extracts source domain for categorization

### 15. **Frontend: Synthesis Initiation (next-frontend/app/page.js)**
- **Function**: `handleSynthesis(searchResults, plan)`
- **Actions**:
  - Sets `researchState` to `'synthesizing'`
  - Prepares synthesis request with search results and plan
  - Calls research synthesis API

### 16. **Frontend API Route: Research Stream Proxy (next-frontend/app/api/research/stream/route.js)**
- **File**: `next-frontend/app/api/research/stream/route.js`
- **Function**: `POST` handler
- **Actions**:
  - Forwards request to FastAPI backend at `http://localhost:8000/research/stream`
  - Creates streaming response for synthesis

### 17. **Backend: Research Synthesis (server/routes/research.py)**
- **File**: `server/routes/research.py`
- **Function**: `research_stream()`
- **Actions**:
  - Creates `ResearchAgent` instance
  - Calls `stream_research_response()` function

### 18. **Backend: AI Synthesis Generation (server/routes/research.py)**
- **File**: `server/routes/research.py`
- **Function**: `stream_research_response(query, plan, search_results)`
- **Process**:
  - Converts search results back to `WebSearchResult` objects
  - Prepares content from all search results
  - Formats synthesis prompt with query, plan, and content
  - Sends request to Ollama API with synthesis-optimized settings:
    - Model: `llama3.2:latest`
    - Context window: 24K tokens (3x larger for synthesis)
    - Temperature: 0.4
    - GPU layers: 50
  - Streams synthesis response back to frontend

### 19. **Frontend: Synthesis Display (next-frontend/app/page.js)**
- **Function**: `handleSynthesis()` (continued)
- **Process**:
  - Receives streaming synthesis response
  - Updates bot message content in real-time
  - Handles streaming errors and completion
  - Sets `researchState` back to `null`

### 20. **Frontend: Final UI Updates**
- **Components**:
  - Research synthesis displayed as final bot message
  - Loading states cleared
  - Research mode remains active for follow-up queries
  - Auto-scroll to latest message

## Key Files Involved

### Frontend Files
- `next-frontend/app/page.js` - Main chat interface and research logic
- `next-frontend/components/ResearchPlan.js` - Research plan display component
- `next-frontend/app/api/research/plan/route.js` - Research plan API proxy
- `next-frontend/app/api/research/execute/route.js` - Research execution API proxy
- `next-frontend/app/api/research/stream/route.js` - Research synthesis API proxy

### Backend Files
- `server/routes/research.py` - Research API endpoints
- `server/research_agent.py` - Research agent implementation
- `server/models.py` - Research data models (ResearchPlanRequest, WebSearchResult, etc.)
- `server/config.py` - Research configuration and prompts
- `server/utils.py` - Web content processing utilities

### External Services
- **Tavily API** - Web search service
- **Ollama API** - LLM for plan generation and synthesis

## Configuration Parameters

### Research Model Settings
- **Plan Generation**: 8K context, 0.3 temperature
- **Synthesis**: 24K context, 0.4 temperature
- **GPU Layers**: 50
- **Max Search Results**: 5 per query
- **Content Length**: 8K characters per source

### Search Configuration
- **Search Depth**: Advanced
- **Relevance Threshold**: 0.1
- **Max Queries**: 4 per research plan
- **Source Types**: Academic, news, expert analysis, technical docs

### System Behavior
- **Streaming**: Real-time synthesis generation
- **Error Handling**: Graceful fallbacks for search failures
- **Plan Refinement**: User can edit generated plans
- **Progress Tracking**: Visual feedback for each research phase

## Research Phases

### Phase 1: Planning
- AI generates comprehensive research plan
- User can review and refine plan
- Plan includes objectives, search strategy, sources, analysis framework

### Phase 2: Execution
- System executes search queries from plan
- Performs web searches using Tavily API
- Processes and filters search results
- Calculates relevance scores

### Phase 3: Synthesis
- AI synthesizes findings from multiple sources
- Generates comprehensive research report
- Follows analysis framework from plan
- Provides structured, well-organized output

## Error Handling

### Search Errors
- Tavily API failures
- Network connectivity issues
- Content processing errors
- Relevance filtering failures

### Synthesis Errors
- Ollama API failures
- Context window limitations
- Prompt formatting errors
- Streaming response issues

### User Experience
- Clear error messages for each phase
- Graceful degradation when services fail
- Option to retry failed operations
- Progress indicators for long-running operations

## Performance Considerations

### Optimization
- Parallel search execution
- Content caching and deduplication
- Relevance-based result filtering
- Streaming response generation

### Resource Management
- Large context windows for synthesis
- Memory-efficient content processing
- Request cancellation support
- Timeout handling for long operations

### Scalability
- Modular research agent architecture
- Configurable search parameters
- Extensible source types
- Pluggable synthesis strategies 