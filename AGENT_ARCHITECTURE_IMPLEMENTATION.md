# Working Three-Agent Architecture Implementation

## Overview

After extensive testing and troubleshooting, we've successfully implemented a **simplified three-agent architecture** that avoids ADK's limitations with complex function calling and async operations. The final working solution prioritizes reliability over complexity.

## Key Implementation Insights

### 1. **ADK Function Calling Limitations Discovered**
- **Problem**: Complex function tools with async Firestore operations were unreliable in ADK
- **Symptom**: Agents would claim to call functions but the calls section in logs showed empty brackets `[]`
- **Root Cause**: ADK's function calling mechanism doesn't work reliably with complex async operations
- **Solution**: Simplified agents to conversational-only, moved all database operations to main app

### 2. **Async Event Loop Conflicts**
- **Problem**: Using `asyncio.run_until_complete()` within ADK's async context caused "this event loop is already running" errors
- **Root Cause**: ADK runs in its own async event loop, cannot nest another event loop
- **Solution**: Removed all async function tools from agents, main app handles all async operations

### 3. **Context Injection Pattern**
- **Problem**: Session state and header-based context were unreliable
- **Solution**: **Rich message content injection** - main app loads all data and provides comprehensive context to agents
- **Benefit**: Agents receive everything they need in the message content

## Final Working Architecture

```
laiers/
├── job_matching_agent/         # Dashboard Agent (Single mount at /adk)
│   ├── __init__.py            # from . import agent
│   └── agent.py               # Conversational guidance agent (no function tools)
├── job_posting_agent/         # Creation Agent (Separate directory)
│   ├── __init__.py            # from . import agent  
│   └── agent.py               # Conversational job creation (no function tools)
├── assessment_agent/          # Evaluation Agent (Separate directory)
│   ├── __init__.py            # from . import agent
│   └── agent.py               # Conversational assessment (no function tools)
└── main.py                    # ALL database operations, structured output parsing
```

## Agent Responsibilities (Simplified)

### 1. job_matching_agent (Dashboard)
- **Location**: Dashboard template chat interface
- **Mount**: `/adk` (single mount point)
- **Purpose**: Welcome users, provide guidance, general job matching advice
- **Pattern**: Pure conversational agent, no function tools
- **Context**: Receives user type and basic profile info in message content

### 2. job_posting_agent (Creation)
- **Location**: Create opportunity template chat interface
- **Purpose**: AI-guided job creation through conversation
- **Pattern**: Collects information conversationally, returns structured `OPPORTUNITY_READY` format
- **Main App Integration**: `parse_opportunity_from_response()` extracts data and creates in Firestore
- **Key Insight**: No direct database access - agent focuses on conversation, main app handles persistence

### 3. assessment_agent (Evaluation)  
- **Location**: Opportunity detail template assessment interface
- **Purpose**: Candidate evaluation based on rich context provided by main app
- **Pattern**: Receives comprehensive opportunity + application data in message content
- **Context Injection**: Job details, survey questions, candidate responses all provided upfront
- **Key Insight**: No async function calls - immediate analysis based on injected data

## Technical Implementation Patterns

### Simplified Agent Pattern
```python
# All agents follow this simple pattern
agent = LlmAgent(
    name="agent_name",
    model="gemini-2.0-flash-lite",
    instruction="""Clear conversational instructions without function calling complexity""",
    tools=[]  # NO FUNCTION TOOLS - Pure conversational agents
)
```

### Main App Database Integration
```python
# Main app handles ALL database operations
@app.post("/api/opportunities/create")
async def create_opportunity_chat(message: str, user=Depends(require_auth)):
    # 1. Call conversational job_posting_agent
    agent_response = await call_adk_agent("job_posting_agent", message, user_context)
    
    # 2. Parse structured output from agent response
    if "OPPORTUNITY_READY" in agent_response:
        opportunity_data = parse_opportunity_from_response(agent_response)
        
        # 3. Main app creates in Firestore (reliable async handling)
        await firestore_service.create_opportunity(opportunity_data)
    
    return template_response(agent_response)
```

### Rich Context Injection Pattern
```python
# Assessment endpoint provides comprehensive context
@app.post("/api/opportunities/{id}/assess")
async def assess_candidates(opportunity_id: str, message: str, user=Depends(require_auth)):
    # 1. Main app loads ALL data from Firestore
    opportunity = await firestore_service.get_opportunity(opportunity_id)
    applications = await firestore_service.get_applications_by_opportunity(opportunity_id)
    
    # 2. Create rich context message
    assessment_context = f"""
**Job Opportunity:** {opportunity.get('title')}
**Company:** {company_name}
**Description:** {opportunity.get('description')}
**Requirements:** {opportunity.get('requirements')}

**Survey Questions:**
{format_survey_questions(opportunity.get('survey_questions', []))}

**Candidate Applications:** {len(applications)} total
{format_candidate_data(applications)}

**User Question:** {message}
"""
    
    # 3. Send rich context to conversational assessment agent
    agent_response = await call_adk_agent("assessment_agent", assessment_context, user_context)
    
    return template_response(agent_response)
```

## Agent Mounting Strategy

### Single Mount Point (Working Solution)
```python
# Mount single ADK app with job_matching_agent
adk_app = get_fast_api_app(
    agents_dir="job_matching_agent",
    allow_origins=["*"] if ENVIRONMENT == "development" else [],
    web=True  # Dev UI at /adk/dev-ui/
)
app.mount("/adk", adk_app)

# Route different agent conversations through different endpoints
# /api/chat → job_matching_agent
# /api/opportunities/create → job_posting_agent (via HTTP call)
# /api/opportunities/{id}/assess → assessment_agent (via HTTP call)
```

### Agent Communication Pattern
```python
async def call_adk_agent(agent_name: str, message: str, user_context: dict):
    """Generic ADK agent communication"""
    payload = {
        "appName": agent_name,
        "userId": user_context["uid"],
        "sessionId": f"session_{user_context['uid']}_{agent_name}",
        "newMessage": {"role": "user", "parts": [{"text": message}]},
        "streaming": False
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(f"http://localhost:8000/adk/run", json=payload)
        if response.status_code == 200:
            return response.json()[0]["content"]["parts"][0]["text"]
        else:
            raise Exception(f"ADK error: {response.status_code}")
```

## Key Benefits of Simplified Architecture

### ✅ **Reliability First**
- No complex function calling that might fail silently
- All database operations handled by proven Firestore integration in main app
- Predictable error handling and logging

### ✅ **Clear Separation of Concerns**
- Agents focus purely on conversation and analysis
- Main app handles all data persistence and complex async operations
- Easier to debug and maintain

### ✅ **Proven Integration Patterns**
- Uses established FastAPI + Firestore patterns that we know work
- ADK provides conversational AI, main app provides data layer
- No mixing of ADK limitations with database complexity

### ✅ **Context-Rich Interactions**
- Agents receive comprehensive context in message content
- No reliance on session state or headers
- Immediate analysis capabilities without async function calls

## Development URLs (Working)

### Agent Testing
- **Primary Agent**: `http://localhost:8000/adk/dev-ui/` (job_matching_agent)
- **Complete Flow Test**: `http://localhost:8000/test/adk-complete-flow`

### Application Endpoints
- **Dashboard Chat**: `POST /api/chat` → job_matching_agent via /adk/run
- **Create Opportunity**: `POST /api/opportunities/create` → job_posting_agent conversation + main app parsing
- **Assess Candidates**: `POST /api/opportunities/{id}/assess` → assessment_agent with rich context

## Success Metrics Achieved

- ✅ **Job Posting Agent**: Successfully collects job information and returns structured data
- ✅ **Main App Integration**: Reliably parses agent responses and creates opportunities in Firestore
- ✅ **Assessment Agent**: Provides immediate candidate analysis based on rich context
- ✅ **No Function Call Failures**: Zero "claimed to call function but didn't" issues
- ✅ **No Async Errors**: Zero "event loop already running" errors
- ✅ **Consistent Context**: Rich message content injection works reliably

## Troubleshooting Insights

### If Agents Stop Working
1. **Check ADK Connection**: Use `/test/adk-complete-flow` endpoint
2. **Verify Single Mount**: Only mount one ADK app, route different conversations through endpoints
3. **No Complex Function Tools**: Keep agents conversational only
4. **Rich Context**: Provide all needed data in message content, don't rely on function calls

### If Database Operations Fail
1. **Main App Handles**: All Firestore operations should be in main app endpoints
2. **Parse Agent Responses**: Look for structured output markers like `OPPORTUNITY_READY`
3. **Error Handling**: Wrap all database operations in try/catch blocks

### Agent Communication Issues
1. **Timeout Handling**: Use 30-second timeouts for complex operations
2. **Session Management**: Different session IDs for different agent types
3. **HTTP Client**: Use httpx.AsyncClient for calling ADK endpoints

## Architecture Philosophy

**"Agents for Conversation, Main App for Data"**

This architecture recognizes ADK's strengths (conversational AI) and limitations (complex function calling) and builds around them. The result is a reliable, maintainable system that provides sophisticated AI-guided user experiences while maintaining data integrity through proven patterns.

The key insight: **Don't try to make ADK do everything. Use it for what it's good at (conversation) and handle the rest with proven FastAPI + Firestore patterns.** 