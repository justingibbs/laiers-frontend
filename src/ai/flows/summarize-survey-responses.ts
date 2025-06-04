'use server';
/**
 * @fileOverview Summarizes survey responses and provides an overall score for each job seeker.
 *
 * - summarizeSurveyResponses - A function that generates a summary of survey responses and an overall score.
 * - SummarizeSurveyResponsesInput - The input type for the summarizeSurveyResponses function.
 * - SummarizeSurveyResponsesOutput - The return type for the summarizeSurveyResponses function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const SummarizeSurveyResponsesInputSchema = z.object({
  jobListing: z.string().describe('The job listing description.'),
  surveyResponses: z
    .record(z.string(), z.string())
    .describe('A map of survey questions to the job seeker\'s responses.'),
  softSkills: z
    .array(z.string())
    .describe(
      'A list of soft skills (Communication, Collaboration, Accountability, Problem-Solving, Adaptability, Initiative, Emotional Intelligence) that the survey focuses on.'
    ),
});
export type SummarizeSurveyResponsesInput = z.infer<typeof SummarizeSurveyResponsesInputSchema>;

const SummarizeSurveyResponsesOutputSchema = z.object({
  summary: z.string().describe('A summary of the survey responses.'),
  overallScore: z.number().describe('An overall score for the job seeker.'),
});
export type SummarizeSurveyResponsesOutput = z.infer<typeof SummarizeSurveyResponsesOutputSchema>;

export async function summarizeSurveyResponses(
  input: SummarizeSurveyResponsesInput
): Promise<SummarizeSurveyResponsesOutput> {
  return summarizeSurveyResponsesFlow(input);
}

const prompt = ai.definePrompt({
  name: 'summarizeSurveyResponsesPrompt',
  input: {schema: SummarizeSurveyResponsesInputSchema},
  output: {schema: SummarizeSurveyResponsesOutputSchema},
  prompt: `You are an expert talent acquisition specialist.

You are provided with a job listing, a set of survey responses from a job seeker, and the key soft skills being assessed.

Based on this information, generate a summary of the job seeker's responses and provide an overall score (out of 100) that reflects their suitability for the role based on the soft skills.

Job Listing: {{{jobListing}}}

Survey Responses:
{{#each (lookup surveyResponses)}}
  Question: {{@key}}
  Response: {{{this}}}
{{/each}}

Soft Skills: {{softSkills}}

Summary:
Overall Score:`, // Ensure the output includes "Summary:" and "Overall Score:"
});

const summarizeSurveyResponsesFlow = ai.defineFlow(
  {
    name: 'summarizeSurveyResponsesFlow',
    inputSchema: SummarizeSurveyResponsesInputSchema,
    outputSchema: SummarizeSurveyResponsesOutputSchema,
  },
  async input => {
    const {output} = await prompt(input);
    return output!;
  }
);
