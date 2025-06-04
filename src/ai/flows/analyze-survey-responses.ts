'use server';

/**
 * @fileOverview Analyzes survey responses for a job seeker and provides insights and scores.
 *
 * - analyzeSurveyResponses - A function that analyzes survey responses.
 * - AnalyzeSurveyResponsesInput - The input type for the analyzeSurveyResponses function.
 * - AnalyzeSurveyResponsesOutput - The return type for the analyzeSurveyResponses function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const AnalyzeSurveyResponsesInputSchema = z.object({
  jobListing: z.string().describe('The job listing description.'),
  softSkills: z.array(z.string()).describe('The top 3 prioritized soft skills for the job.'),
  responses: z.array(
    z.object({
      question: z.string().describe('The survey question.'),
      answer: z.string().describe('The job seeker\'s answer to the question.'),
    })
  ).describe('The job seeker\'s responses to the survey questions.'),
});

export type AnalyzeSurveyResponsesInput = z.infer<typeof AnalyzeSurveyResponsesInputSchema>;

const AnalyzeSurveyResponsesOutputSchema = z.object({
  analysis: z.string().describe('An analysis of the survey responses, providing insights into the job seeker\'s soft skill proficiency.'),
  scores: z.record(z.string(), z.number()).describe('A score for each soft skill, based on the survey responses.'),
  summary: z.string().describe('A summary of the survey responses with an overall score.'),
});

export type AnalyzeSurveyResponsesOutput = z.infer<typeof AnalyzeSurveyResponsesOutputSchema>;

export async function analyzeSurveyResponses(input: AnalyzeSurveyResponsesInput): Promise<AnalyzeSurveyResponsesOutput> {
  return analyzeSurveyResponsesFlow(input);
}

const prompt = ai.definePrompt({
  name: 'analyzeSurveyResponsesPrompt',
  input: {schema: AnalyzeSurveyResponsesInputSchema},
  output: {schema: AnalyzeSurveyResponsesOutputSchema},
  prompt: `You are a hiring expert analyzing survey responses from a job seeker to determine their proficiency in key soft skills for a given job listing.

Job Listing: {{{jobListing}}}

Top Soft Skills: {{#each softSkills}}{{{this}}}{{#unless @last}}, {{/unless}}{{/each}}

Survey Responses:
{{#each responses}}
Question: {{{question}}}
Answer: {{{answer}}}
{{/each}}

Analyze the survey responses, providing insights into the job seeker's soft skill proficiency based on the job listing and identified soft skills. Provide a score (out of 100) for each soft skill, reflecting the job seeker's demonstrated abilities.

Ensure that the analysis and scores are aligned and well-justified by the provided job listing, soft skills, and survey responses.

Output the analysis, scores, and a summary with an overall score.

Ensure that the scores are returned as key value pairs in the ` + '`scores`' + ` field.
For example, the scores field should look like this:
` + '`{ 