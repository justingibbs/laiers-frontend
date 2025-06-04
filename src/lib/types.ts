import type { CreateSkillsSurveyOutput } from '@/ai/flows/create-skills-survey';
import type { AnalyzeSurveyResponsesOutput } from '@/ai/flows/analyze-survey-responses';
import type { SummarizeSurveyResponsesOutput } from '@/ai/flows/summarize-survey-responses';

export interface Job {
  id: string;
  title: string; // User-defined title for the job
  descriptionInput: string;
  generatedListingText?: string;
  survey?: Survey;
  applicants: Applicant[];
  createdAt: number; // Timestamp
}

export interface Survey extends CreateSkillsSurveyOutput {
  // surveyQuestions and topSkills are from CreateSkillsSurveyOutput
}

export interface Applicant {
  id: string; 
  name: string;
  jobId: string;
  responses: Array<{ question: string; answer: string }>;
  analysisOutput?: AnalyzeSurveyResponsesOutput;
  overallScoreData?: SummarizeSurveyResponsesOutput;
  submittedAt: number; // Timestamp
}

export type SoftSkill = 
  | 'Communication'
  | 'Collaboration / Teamwork'
  | 'Accountability / Ownership'
  | 'Problem-Solving'
  | 'Adaptability / Resilience'
  | 'Initiative'
  | 'Emotional Intelligence (EQ)';

export const ALL_SOFT_SKILLS: SoftSkill[] = [
  'Communication',
  'Collaboration / Teamwork',
  'Accountability / Ownership',
  'Problem-Solving',
  'Adaptability / Resilience',
  'Initiative',
  'Emotional Intelligence (EQ)',
];
