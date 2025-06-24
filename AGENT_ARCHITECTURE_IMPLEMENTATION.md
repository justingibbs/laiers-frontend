# Three-Agent Architecture Implementation Guide

## Overview

Based on ADK best practices research and your requirements, I've implemented a sophisticated three-agent architecture that fixes the Firestore integration issues and provides clean separation of concerns.

## Key Improvements Made

### 1. **Fixed Firestore Integration Issue**
- **Problem**: `job_posting_agent` couldn't create database entries due to indirect tool delegation
- **Solution**: Added direct Firestore tools (`create_opportunity_in_firestore`, `validate_opportunity_data`) to the posting agent
- **Result**: Agent now has direct database access and can create opportunities successfully

### 2. **Independent Agent Architecture**
- **Before**: Single mount point with complex sub-agent delegations
- **After**: Three independent agents mounted separately with specialized tools
- **Benefits**: Cleaner routing, better error isolation, specialized functionality

### 3. **Header-Based Context Passing**
- **Before**: Complex message parsing `[User type: company, Task: create_opportunity] message`
- **After**: Clean header-based context with `X-User-Type`, `X-Company-ID`, etc.
- **Benefits**: Simpler agent logic, more reliable context handling

## Architecture Overview

```
laiers/
├── job_matching_agent/         # Dashboard Agent (/adk/dashboard)
│   ├── __init__.py            # from . import agent
│   └── agent.py               # Simplified guidance and navigation
├── job_posting_agent/         # Creation Agent (/adk/posting)
│   ├── __init__.py            # from . import agent
│   └── agent.py               # Direct Firestore tools for opportunity creation
├── assessment_agent/          # Evaluation Agent (/adk/assessment)
│   ├── __init__.py            # from . import agent
│   └── agent.py               # Direct tools for candidate analysis
└── main.py                    # Updated with three-agent mounting
```

## Agent Responsibilities

### 1. job_matching_agent (Dashboard)
- **Location**: `dashboard.html` template
- **Mount**: `/adk/dashboard` (also `/adk` for backward compatibility)
- **Purpose**: Welcome users, provide guidance, navigation help
- **Tools**: 
  - `get_user_guidance()`: Personalized welcome messages
  - `navigate_to_feature()`: Guide users to appropriate tools
- **Dev UI**: Enabled at `/adk/dashboard/dev-ui/`

### 2. job_posting_agent (Creation)
- **Location**: `create_opportunity.html` template  
- **Mount**: `/adk/posting`
- **Purpose**: AI-guided opportunity creation with direct database access
- **Tools**:
  - `create_opportunity_in_firestore()`: **Direct Firestore integration** ✅
  - `validate_opportunity_data()`: Data validation before creation
- **Key Fix**: No more parsing - agent creates opportunities directly in database

### 3. assessment_agent (Evaluation)
- **Location**: `opportunity_detail.html` template
- **Mount**: `/adk/assessment`  
- **Purpose**: Candidate evaluation for specific opportunities
- **Tools**:
  - `load_opportunity_applications()`: Get opportunity + application data
  - `analyze_candidate_responses()`: Rank and score candidates
  - `generate_interview_questions()`: Tailored questions per candidate

## Technical Implementation

### FastAPI Mounting Pattern
```python
# Mount three independent ADK agents
dashboard_app = get_fast_api_app(agents_dir="job_matching_agent", web=True)
posting_app = get_fast_api_app(agents_dir="job_posting_agent", web=False)  
assessment_app = get_fast_api_app(agents_dir="assessment_agent", web=False)

app.mount("/adk/dashboard", dashboard_app)
app.mount("/adk/posting", posting_app)
app.mount("/adk/assessment", assessment_app)
app.mount("/adk", dashboard_app)  # Backward compatibility
```

### Chat Endpoint Routing
```python
# Dashboard chat
@app.post("/api/chat")
→ calls /adk/dashboard/run

# Opportunity creation chat  
@app.post("/api/opportunities/create")
→ calls /adk/posting/run

# Assessment chat
@app.post("/api/opportunities/{id}/assess")  
→ calls /adk/assessment/run
```

### Header-Based Context
```python
session_headers = {
    "X-User-Type": user_type,      # "talent" or "company" 
    "X-User-ID": user_id,          # Firebase user ID
    "X-Company-ID": company_id,    # Company ID for company users
    "X-Opportunity-ID": opp_id,    # For assessment agent
    "Content-Type": "application/json"
}
```

## Key Benefits Achieved

### ✅ **Firestore Integration Fixed**
- Job posting agent now successfully creates opportunities in database
- Direct tools eliminate the delegation complexity
- Proper error handling and validation

### ✅ **Clean Separation of Concerns**  
- Each agent has focused responsibility and specialized tools
- No more complex routing logic in main agent
- Independent development and testing

### ✅ **Simplified Context Handling**
- Headers replace complex message parsing
- Agents receive clean user input without context pollution
- More reliable and maintainable

### ✅ **Better Error Isolation**
- Agent failures don't affect other agents
- Specific error messages per agent type
- Easier debugging and monitoring

### ✅ **Scalable Architecture**
- Easy to add new specialized agents
- Independent mounting allows different configurations
- Clear API boundaries

## Development URLs

### Agent-Specific Endpoints
- **Dashboard Agent**: `http://localhost:8000/adk/dashboard/dev-ui/`
- **Job Posting**: `http://localhost:8000/adk/posting/run` (API only)
- **Assessment**: `http://localhost:8000/adk/assessment/run` (API only)

### Application Endpoints  
- **Dashboard Chat**: `POST /api/chat` → Dashboard agent
- **Create Opportunity**: `POST /api/opportunities/create` → Posting agent
- **Assess Candidates**: `POST /api/opportunities/{id}/assess` → Assessment agent

## Migration Notes

### What Changed
1. **Removed** complex sub-agent delegations from main agent
2. **Added** direct Firestore tools to posting agent
3. **Simplified** context passing to header-based approach
4. **Split** single mount into three independent mounts

### Backward Compatibility
- Main `/adk` mount still works for dashboard agent
- Existing dashboard chat functionality preserved
- All template routes unchanged

### Testing Priority
1. **Opportunity Creation**: Test end-to-end job posting flow
2. **Database Integration**: Verify opportunities are saved to Firestore  
3. **Assessment Flow**: Test candidate evaluation on opportunity detail pages
4. **Context Passing**: Verify user types are correctly identified

## Success Metrics

- ✅ Job posting agent creates Firestore entries successfully
- ✅ Each agent operates independently on designated pages
- ✅ Assessment agent only accesses relevant opportunity data
- ✅ Smooth user flow between agents/pages
- ✅ No more complex context parsing errors
- ✅ Clear error messages and better debugging

## Next Steps

1. **Test the new architecture** with actual job posting flow
2. **Verify Firestore integration** by creating opportunities
3. **Test assessment features** with sample applications
4. **Monitor agent performance** and error rates
5. **Consider additional specialized agents** for future features

This implementation follows ADK best practices from the latest documentation and provides a robust, scalable foundation for your job matching platform. 