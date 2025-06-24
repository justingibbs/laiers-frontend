# assessment_agent/agent.py
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

def load_opportunity_applications(opportunity_id: str) -> Dict[str, Any]:
    """Load opportunity details and all applications for assessment"""
    try:
        # Import here to avoid circular imports
        from utils.firestore import FirestoreService
        import asyncio
        
        firestore_service = FirestoreService()
        loop = asyncio.get_event_loop()
        
        # Get opportunity details
        opportunity = loop.run_until_complete(firestore_service.get_opportunity(opportunity_id))
        if not opportunity:
            return {
                "success": False,
                "error": f"Opportunity {opportunity_id} not found",
                "message": "❌ Could not find the specified opportunity."
            }
        
        # Get all applications
        applications = loop.run_until_complete(firestore_service.get_applications_by_opportunity(opportunity_id))
        
        return {
            "success": True,
            "opportunity": opportunity,
            "applications": applications,
            "applications_count": len(applications),
            "message": f"✅ Loaded opportunity '{opportunity.get('title')}' with {len(applications)} applications"
        }
        
    except Exception as e:
        logger.error(f"Error loading opportunity data: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Error loading opportunity data: {str(e)}"
        }

def analyze_candidate_responses(
    candidate_responses: List[Dict[str, Any]],
    job_requirements: str,
    survey_questions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Analyze and rank candidate responses against job requirements"""
    try:
        candidate_analyses = []
        
        for candidate in candidate_responses:
            applicant_name = candidate.get('applicant_name', 'Unknown')
            applicant_email = candidate.get('applicant_email', 'Unknown')
            survey_responses = candidate.get('survey_responses', {})
            
            # Analyze each response
            response_quality = []
            total_score = 0
            
            for i, question in enumerate(survey_questions):
                question_key = f"question_{i}"
                response = survey_responses.get(question_key, "")
                
                # Basic scoring criteria
                if not response or response.lower().strip() in ["", "n/a", "none", "no"]:
                    score = 0
                    quality = "No response"
                elif len(response.strip()) < 20:
                    score = 2
                    quality = "Brief response"
                elif len(response.strip()) < 100:
                    score = 3
                    quality = "Moderate response"
                else:
                    score = 4
                    quality = "Detailed response"
                
                response_quality.append({
                    "question": question.get('question', f'Question {i+1}'),
                    "response": response,
                    "score": score,
                    "quality": quality
                })
                total_score += score
            
            # Calculate overall fit score
            max_possible_score = len(survey_questions) * 4
            fit_percentage = (total_score / max_possible_score) * 100 if max_possible_score > 0 else 0
            
            if fit_percentage >= 80:
                fit_level = "Excellent"
            elif fit_percentage >= 65:
                fit_level = "Good"
            elif fit_percentage >= 50:
                fit_level = "Fair"
            else:
                fit_level = "Poor"
            
            candidate_analyses.append({
                "applicant_name": applicant_name,
                "applicant_email": applicant_email,
                "fit_level": fit_level,
                "fit_percentage": round(fit_percentage, 1),
                "total_score": total_score,
                "max_score": max_possible_score,
                "response_quality": response_quality
            })
        
        # Sort by fit percentage (highest first)
        candidate_analyses.sort(key=lambda x: x["fit_percentage"], reverse=True)
        
        return {
            "success": True,
            "candidate_count": len(candidate_analyses),
            "analyses": candidate_analyses,
            "message": f"✅ Analyzed {len(candidate_analyses)} candidates successfully"
        }
        
    except Exception as e:
        logger.error(f"Error analyzing candidates: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Error analyzing candidates: {str(e)}"
        }

def generate_interview_questions(
    candidate_analysis: Dict[str, Any],
    job_requirements: str,
    opportunity_title: str
) -> Dict[str, Any]:
    """Generate tailored interview questions for a specific candidate"""
    try:
        candidate_name = candidate_analysis.get('applicant_name', 'Candidate')
        fit_level = candidate_analysis.get('fit_level', 'Unknown')
        response_quality = candidate_analysis.get('response_quality', [])
        
        # Base interview questions
        questions = [
            f"Tell me about your interest in the {opportunity_title} position.",
            "What attracted you to our company and this role specifically?"
        ]
        
        # Add follow-up questions based on their responses
        for item in response_quality:
            if item['score'] <= 2:  # Poor/brief responses
                questions.append(f"I'd like to dive deeper into your response about '{item['question'][:50]}...' - can you provide a specific example?")
        
        # Add questions based on fit level
        if fit_level == "Excellent":
            questions.extend([
                "Your application shows strong alignment with our requirements. What would success look like for you in the first 90 days?",
                "How do you see yourself contributing to our team culture?"
            ])
        elif fit_level == "Good":
            questions.extend([
                "Your background looks promising. Tell me about a challenging project you've worked on that relates to this role.",
                "What areas would you want to develop further in this position?"
            ])
        elif fit_level in ["Fair", "Poor"]:
            questions.extend([
                "Help me understand how your background connects to the requirements of this role.",
                "What steps would you take to quickly get up to speed in areas where you might need development?"
            ])
        
        # Add behavioral questions based on job requirements
        if "leadership" in job_requirements.lower():
            questions.append("Describe a time when you had to lead a team through a difficult situation.")
        
        if "communication" in job_requirements.lower():
            questions.append("Give me an example of how you've handled miscommunication in a professional setting.")
        
        return {
            "success": True,
            "candidate_name": candidate_name,
            "fit_level": fit_level,
            "questions": questions,
            "question_count": len(questions),
            "message": f"✅ Generated {len(questions)} tailored interview questions for {candidate_name}"
        }
        
    except Exception as e:
        logger.error(f"Error generating interview questions: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Error generating interview questions: {str(e)}"
        }

# Create the assessment agent with candidate evaluation tools
assessment_agent = LlmAgent(
    name="assessment_agent",
    model="gemini-2.0-flash-lite",
    description="Specialized agent for evaluating job candidates with direct access to application data. Analyzes survey responses, ranks candidates, and suggests interview questions.",
    instruction="""You are a candidate assessment specialist with direct access to application data. You help company users evaluate job applicants objectively and efficiently.

Your capabilities include:
- Loading opportunity and application data using load_opportunity_applications
- Analyzing candidate responses against job requirements using analyze_candidate_responses  
- Generating tailored interview questions using generate_interview_questions

WORKFLOW:
1. **Load Data**: Use load_opportunity_applications with the opportunity_id to get all relevant data
2. **Analyze Candidates**: Use analyze_candidate_responses to evaluate and rank all applicants
3. **Generate Questions**: Use generate_interview_questions for specific candidates when requested

ANALYSIS CRITERIA:
- Response quality and depth
- Relevance to job requirements
- Communication skills evident in responses
- Specific examples and achievements
- Cultural fit indicators

When evaluating candidates:
- Be objective and focus on job-relevant criteria
- Look for specific examples and quantifiable achievements
- Consider communication skills and attention to detail
- Highlight both strengths and areas of concern
- Provide actionable insights for hiring decisions

Always provide balanced assessments and help hiring managers make informed decisions while avoiding bias.

Use your tools proactively - don't just describe what you could do, actually use them to provide real analysis and insights.""",
    tools=[
        FunctionTool(load_opportunity_applications),
        FunctionTool(analyze_candidate_responses),
        FunctionTool(generate_interview_questions)
    ],
)

# Required for ADK discovery
root_agent = assessment_agent 