# job_matching_agent/__init__.py
from . import agent

# job_matching_agent/agent.py
from google.adk.agents import Agent
from .job_posting_agent import job_posting_agent

# This MUST be named 'root_agent' for ADK to discover it
root_agent = Agent(
    name="job_matching_agent",
    model="gemini-2.0-flash-lite",
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
Hand off to the specialized job posting creation agent.

Always maintain a professional, helpful, and encouraging tone. Ask follow-up questions to better understand their specific needs and provide personalized advice.""",
    sub_agents=[job_posting_agent]
)

# Optional: Add tools for the agent
def get_user_context(user_type: str, email: str) -> dict:
    """Get context about the current user for personalized responses"""
    return {
        "user_type": user_type,
        "email": email,
        "platform": "job_matching_platform"
    }

# You can add more tools here as needed
# root_agent.tools = [get_user_context]