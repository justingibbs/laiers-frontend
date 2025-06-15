from google.adk.agents.llm_agent import Agent
from google.adk.runners import Runner
from google.adk.artifacts import GcsArtifactService
from google.adk.sessions import InMemorySessionService
import os

# Configure agent
job_matching_agent = Agent(
    name="job_matching_agent",
    model="gemini-2.0-flash-exp",
    instruction="""You are a job matching assistant. 
    - For 'talent' users: Help with resume review, job search, interview prep
    - For 'company' users: Help with job posting, candidate screening, hiring advice
    Adapt your responses based on user_type in the context.
    Always be professional, concise, and helpful.""",
    description="AI assistant for job matching and career guidance"
)

# Configure artifact service for file handling
artifact_service = GcsArtifactService(
    bucket_name=os.getenv("ADK_BUCKET_NAME")
)

# Create session service
session_service = InMemorySessionService()

# Create runner
runner = Runner(
    agent=job_matching_agent,
    artifact_service=artifact_service,
    app_name="job-matching-app",
    session_service=session_service
) 