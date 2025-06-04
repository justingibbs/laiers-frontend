'use server';

/**
 * @fileOverview This file defines a Genkit flow for creating a skills survey based on a job listing.
 *
 * - createSkillsSurvey - A function that takes a job listing as input and returns a survey.
 * - CreateSkillsSurveyInput - The input type for the createSkillsSurvey function.
 * - CreateSkillsSurveyOutput - The return type for the createSkillsSurvey function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const CreateSkillsSurveyInputSchema = z.object({
  jobListing: z
    .string()
    .describe('The job listing to create a skills survey for.'),
});
export type CreateSkillsSurveyInput = z.infer<typeof CreateSkillsSurveyInputSchema>;

const CreateSkillsSurveyOutputSchema = z.object({
  surveyQuestions: z
    .array(z.string())
    .describe('An array of survey questions based on the top 3 soft skills.'),
  topSkills: z
    .array(z.string())
    .describe('An array of the top 3 soft skills identified from the job listing.'),
});
export type CreateSkillsSurveyOutput = z.infer<typeof CreateSkillsSurveyOutputSchema>;

export async function createSkillsSurvey(input: CreateSkillsSurveyInput): Promise<CreateSkillsSurveyOutput> {
  return createSkillsSurveyFlow(input);
}

const softSkills = [
  'Communication',
  'Collaboration / Teamwork',
  'Accountability / Ownership',
  'Problem-Solving',
  'Adaptability / Resilience',
  'Initiative',
  'Emotional Intelligence (EQ)',
];

const prompt = ai.definePrompt({
  name: 'createSkillsSurveyPrompt',
  input: {schema: CreateSkillsSurveyInputSchema},
  output: {schema: CreateSkillsSurveyOutputSchema},
  prompt: `You are a helpful AI assistant that helps hiring managers create skills surveys.  You will be provided with a job listing, and you will identify the top 3 soft skills required for this role from the following options: ${softSkills.join( ", " )}.  Then, you will create a 10-question survey that can help extrapolate how a job candidate would handle these top 3 soft skills.  The survey questions should be designed to reveal insights into a candidate's proficiency in these areas. Make sure questions are easily understood by candidates.

Job Listing: {{{jobListing}}}`,
});

const createSkillsSurveyFlow = ai.defineFlow(
  {
    name: 'createSkillsSurveyFlow',
    inputSchema: CreateSkillsSurveyInputSchema,
    outputSchema: CreateSkillsSurveyOutputSchema,
  },
  async input => {
    const {output} = await prompt(input);
    return output!;
  }
);
