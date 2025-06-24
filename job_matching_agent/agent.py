# job_matching_agent/agent.py
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from typing import Optional

MODEL = "gemini-2.0-flash-lite"

def get_user_guidance(user_type: str, task: Optional[str] = None) -> str:
    """Provide user guidance based on their type and current context"""
    if user_type == "talent":
        return """
**Welcome to Laiers.ai! I'm here to help with your job search.**

As a talent user, I can assist you with:
• **Resume review and optimization** - Get tips to make your resume stand out
• **Job search strategies** - Learn effective ways to find opportunities
• **Interview preparation** - Practice and get guidance for interviews
• **Skill development** - Identify areas to improve and grow
• **Career advancement** - Plan your next career moves
• **Application tips** - Best practices for job applications

**Ready to explore opportunities?** [Browse all available jobs](/opportunities)

What would you like help with today?
        """
    elif user_type == "company":
        if task == "create_opportunity":
            return """
**Let's create a new job opportunity!**

I'll guide you through the process step-by-step:
1. Job title and description
2. Requirements and qualifications
3. Location and employment type
4. Key soft skills identification
5. Survey question creation
6. Final review and publishing

This specialized agent will help you create a complete, professional job posting with screening questions to attract the right candidates.

**What position would you like to create?** Please provide the job title and any details you have.
            """
        elif task == "assess_candidates":
            return """
**Candidate Assessment Dashboard**

I'll help you evaluate applicants for this opportunity:
• **Load and review** all candidate applications
• **Analyze responses** against job requirements  
• **Rank candidates** by fit and qualifications
• **Generate interview questions** tailored to each candidate
• **Provide recommendations** for next steps

**Ready to assess?** Tell me what specific aspect you'd like to focus on - overall ranking, specific candidate review, or interview preparation.
            """
        else:
            return """
**Welcome to your Company Dashboard!**

As a company user, I can help you with:
• **Creating job opportunities** - Use our AI-guided posting system
• **Managing applications** - Review and assess candidates
• **Hiring best practices** - Get expert recruitment advice
• **Candidate screening** - Effective evaluation strategies
• **Employer branding** - Attract top talent
• **Interview optimization** - Improve your hiring process

**Quick Actions:**
• Use the "Create Opportunity" button on your company page
• View your active opportunities from your company dashboard
• Browse the opportunities page to see how your postings appear to candidates

What can I help you with today?
            """
    else:
        return "Welcome to Laiers.ai! Please let me know if you're looking for job opportunities (talent) or hiring candidates (company), and I'll provide personalized guidance."

def navigate_to_feature(destination: str, context: dict) -> str:
    """Provide navigation guidance to specific features"""
    user_type = context.get('user_type', 'unknown')
    company_id = context.get('company_id')
    
    if destination == "create_opportunity" and user_type == "company":
        return """
**Ready to create an opportunity?**

Navigate to your company page and click the "Create New Opportunity" button to get started.

This will take you to our AI-guided job posting system where you'll work with a specialized agent to:
• Define job requirements and responsibilities
• Identify key soft skills needed
• Create behavioral interview questions
• Publish a professional opportunity listing

The process takes about 5-10 minutes and results in a complete job posting ready to attract qualified candidates.
        """
    elif destination == "opportunities_list" and user_type == "talent":
        return f"""
**Explore available opportunities!**

Browse all current job openings: [View All Opportunities](/opportunities)

You'll see:
• Complete job descriptions and requirements
• Company information and culture
• Application surveys tailored to each role
• Direct application submission
• Real-time application status

Find your perfect match and apply directly through our platform!
        """
    elif destination == "company_dashboard" and user_type == "company":
        return """
**Visit your company dashboard:**

Navigate to your company page using the main navigation or dashboard.

From there you can:
• View all your active job postings
• See application counts and status
• Access candidate assessments
• Create new opportunities
• Manage your company profile

Your central hub for all hiring activities!
        """
    else:
        return "I can help guide you to the right section. What specific feature are you looking for?"

# Simplified job matching agent focused on dashboard interactions
job_matching_agent = LlmAgent(
    name="job_matching_agent",
    model=MODEL,
    description="Dashboard agent that provides guidance and navigation for talent and company users on the job matching platform.",
    instruction="""You are the main dashboard assistant for Laiers.ai, a professional job matching platform.

**Your Role:**
- Welcome users and provide personalized guidance
- Help users navigate to appropriate features
- Offer general advice for job searching (talent) or hiring (company)
- Direct users to specialized tools and agents

**Key Context:**
Users have a user_type ('talent' or 'company') and may have specific tasks:
- talent: Looking for jobs, career advice, application help
- company: Creating opportunities, assessing candidates, hiring guidance

**Important Navigation:**
- For opportunity creation: Direct users to their company dashboard creation flow
- For candidate assessment: Available on opportunity detail pages
- For job browsing: Direct to `/opportunities`

**Your Approach:**
1. Use get_user_guidance to provide relevant welcome messages and options
2. Use navigate_to_feature to help users reach specific tools
3. Offer helpful, actionable advice within your expertise
4. Be encouraging and professional

**What you DON'T do:**
- Create opportunities directly (that's handled by the specialized posting agent)
- Assess candidates directly (that's handled by the specialized assessment agent)
- Make hiring decisions or provide specific candidate rankings

Instead, guide users to the right tools and provide general best practices and advice.""",
    tools=[
        FunctionTool(get_user_guidance),
        FunctionTool(navigate_to_feature)
    ],
)

# This MUST be named 'root_agent' for ADK to discover it
root_agent = job_matching_agent