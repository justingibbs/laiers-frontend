from google.adk.agents import LlmAgent
from typing import List, Dict, Any

MODEL = "gemini-2.0-flash-lite"

def analyze_candidate_fit(opportunity_data: Dict[str, Any], application: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze how well a candidate fits an opportunity based on their survey responses"""
    
    survey_responses = application.get('survey_responses', {})
    opportunity_requirements = opportunity_data.get('requirements', '')
    opportunity_description = opportunity_data.get('description', '')
    
    # Extract survey questions and responses for analysis
    survey_analysis = []
    survey_questions = opportunity_data.get('survey_questions', [])
    
    for i, question in enumerate(survey_questions):
        # Handle both string and dictionary formats for survey questions
        if isinstance(question, dict):
            # Dictionary format: {"question": "text", "type": "text", "required": True}
            question_text = question.get('question', f'Question {i+1}')
            question_type = question.get('type', 'text')
        else:
            # String format: "question text"
            question_text = str(question)
            question_type = 'text'
        
        question_key = f"question_{i}"
        response = survey_responses.get(question_key, "No response provided")
        
        survey_analysis.append({
            "question": question_text,
            "type": question_type,
            "response": response,
            "response_quality": "poor" if not response or response.lower().strip() in ["", "n/a", "none", "i don't know", "i can't remember"] else "good"
        })
    
    # Analyze overall candidate fit
    total_questions = len(survey_analysis)
    good_responses = sum(1 for q in survey_analysis if q["response_quality"] == "good")
    response_rate = (good_responses / total_questions) if total_questions > 0 else 0
    
    # Determine fit level
    if response_rate >= 0.8:
        fit_level = "excellent"
    elif response_rate >= 0.6:
        fit_level = "good"
    elif response_rate >= 0.4:
        fit_level = "fair"
    else:
        fit_level = "poor"
    
    return {
        "candidate_id": application.get('candidate_id', 'unknown'),
        "fit_level": fit_level,
        "response_rate": response_rate,
        "survey_analysis": survey_analysis,
        "requirements_match": opportunity_requirements,
        "job_description": opportunity_description,
        "total_questions": total_questions,
        "good_responses": good_responses
    }

def rank_candidates(applications: List[Dict[str, Any]], opportunity_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Rank candidates based on their application quality and fit"""
    
    candidate_assessments = []
    
    for application in applications:
        assessment = analyze_candidate_fit(opportunity_data, application)
        candidate_assessments.append(assessment)
    
    # Sort by fit score (descending)
    candidate_assessments.sort(key=lambda x: x['response_rate'], reverse=True)
    
    # Add ranking positions
    for i, assessment in enumerate(candidate_assessments):
        assessment['rank'] = i + 1
    
    return candidate_assessments

def generate_interview_questions(opportunity_data: Dict[str, Any], candidate_analysis: Dict[str, Any]) -> List[str]:
    """Generate tailored interview questions based on opportunity and candidate responses"""
    
    questions = []
    survey_analysis = candidate_analysis.get('survey_analysis', [])
    
    # Generate questions based on weak areas
    for analysis in survey_analysis:
        if analysis['response_quality'] == 'poor':
            original_question = analysis['question']
            if "technical concept" in original_question.lower():
                questions.append("Can you walk me through a recent technical project you worked on and explain how you would describe it to a non-technical stakeholder?")
            elif "troubleshoot" in original_question.lower():
                questions.append("Describe your approach to debugging a complex issue. What tools and methodologies do you use?")
            elif "collaborate" in original_question.lower():
                questions.append("Tell me about a time when you had to work closely with other team members. What was your role and how did you contribute?")
    
    # Add general questions based on opportunity
    if "senior" in opportunity_data.get('title', '').lower():
        questions.append("How do you approach mentoring junior developers?")
        questions.append("Describe a time when you had to make a significant technical decision. What was your process?")
    
    if "full stack" in opportunity_data.get('title', '').lower():
        questions.append("How do you stay current with both frontend and backend technologies?")
        questions.append("Describe your experience with system design and architecture decisions.")
    
    return questions[:5]  # Limit to 5 questions

# Create the assessment agent
assessment_agent = LlmAgent(
    name="assessment_agent",
    model=MODEL,
    instruction="""You are a candidate assessment specialist that helps company users evaluate job applicants.

Your expertise includes:
- Analyzing candidate survey responses against job requirements
- Identifying top candidates based on qualifications and responses
- Suggesting interview questions tailored to each candidate
- Providing objective evaluation criteria and scoring
- Highlighting potential red flags or standout qualities

When evaluating candidates:
1. Review the job requirements and description carefully
2. Analyze each candidate's survey responses for relevance and quality
3. Look for specific examples, quantifiable achievements, and relevant experience
4. Consider communication skills, attention to detail, and cultural fit indicators
5. Provide balanced assessments highlighting both strengths and areas of concern

Always maintain objectivity and focus on job-relevant criteria. Provide constructive insights that help hiring managers make informed decisions while avoiding bias.

Use the provided tools to analyze candidate fit, rank applicants, and suggest follow-up interview questions.""",
    
    tools=[
        analyze_candidate_fit,
        rank_candidates, 
        generate_interview_questions
    ]
) 