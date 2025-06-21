# job_matching_agent/agent.py
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from .job_posting_agent import job_posting_agent

MODEL = "gemini-2.0-flash-lite"

def get_user_context(message: str) -> dict:
    """Extract user context from the message format: [User type: company, Task: create_opportunity, ...] message"""
    context = {
        "user_type": "unknown",
        "task": None,
        "company_name": None,
        "company_id": None,
        "clean_message": message
    }
    
    # Parse context from message format like: [User type: company, Task: create_opportunity, Company: Name, Company ID: id] actual message
    if message.startswith('[') and ']' in message:
        try:
            context_part = message[1:message.index(']')]
            actual_message = message[message.index(']') + 1:].strip()
            context["clean_message"] = actual_message
            
            # Parse key-value pairs
            for part in context_part.split(', '):
                if ': ' in part:
                    key, value = part.split(': ', 1)
                    if key.lower() == "user type":
                        context["user_type"] = value.lower()
                    elif key.lower() == "task":
                        context["task"] = value
                    elif key.lower() == "company":
                        context["company_name"] = value
                    elif key.lower() == "company id":
                        context["company_id"] = value
        except Exception:
            # If parsing fails, just return the original message
            pass
    
    return context

def analyze_user_needs(user_type: str, task: str = None) -> str:
    """Analyze what the user likely needs based on their type and task"""
    if user_type == "talent":
        return """
        Talent users typically need:
        - Resume review and optimization tips
        - Job search strategies and guidance
        - Interview preparation and practice
        - Skill development recommendations
        - Career advancement advice
        - Application tips and best practices
        """
    elif user_type == "company":
        if task == "create_opportunity":
            return """
            Company user creating opportunity needs:
            - Use the job_posting_agent tool for complete workflow
            - The tool will guide through job details, requirements, and logistics
            - Will identify critical soft skills for the role
            - Will generate behavioral interview questions
            - Will create structured opportunity ready for publishing
            """
        else:
            return """
            Company users typically need:
            - Help writing effective job descriptions
            - Candidate screening and evaluation guidance  
            - Hiring best practices and strategies
            - Employer branding advice
            - Recruitment process optimization
            - Interview question development
            """
    else:
        return "Unknown user type - please provide more context about how I can help you."

job_matching_coordinator = LlmAgent(
    name="job_matching_coordinator",
    model=MODEL,
    description="Main job matching assistant that handles talent and company needs, with specialized sub-agents for complex tasks.",
    instruction="""You are a job matching assistant for a professional platform.

Context: You will receive user information including their user_type ('talent' or 'company') and potentially a task type.

For 'talent' users:
- Help with resume review and optimization
- Provide job search strategies and tips
- Offer interview preparation guidance
- Suggest skill development opportunities
- Answer career-related questions

For 'company' users:
- Assist with writing effective job descriptions
- Provide candidate screening and evaluation guidance
- Offer hiring best practices and strategies
- Help with employer branding advice
- Support recruitment process optimization

For 'company' users with Task: 'create_opportunity':
IMMEDIATELY use the job_posting_agent tool. Do not create job opportunities yourself - always delegate this task to the job_posting_agent tool which specializes in the complete workflow including soft skills identification and behavioral interview question creation.

Use the get_user_context tool to understand who you're talking to and the analyze_user_needs tool to provide appropriate guidance.

Always maintain a professional, helpful, and encouraging tone. Ask follow-up questions to better understand their specific needs and provide personalized advice.""",
    tools=[
        get_user_context,
        analyze_user_needs,
        AgentTool(agent=job_posting_agent),
    ],
)

# This MUST be named 'root_agent' for ADK to discover it
root_agent = job_matching_coordinator