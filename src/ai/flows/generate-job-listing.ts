'use server';

/**
 * @fileOverview A job listing generation AI agent.
 *
 * - generateJobListing - A function that handles the job listing generation process.
 * - GenerateJobListingInput - The input type for the generateJobListing function.
 * - GenerateJobListingOutput - The return type for the generateJobListing function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const GenerateJobListingInputSchema = z.object({
  jobDescription: z.string().describe('The description of the job.'),
});
export type GenerateJobListingInput = z.infer<typeof GenerateJobListingInputSchema>;

const GenerateJobListingOutputSchema = z.object({
  jobListing: z.string().describe('The generated job listing.'),
});
export type GenerateJobListingOutput = z.infer<typeof GenerateJobListingOutputSchema>;

export async function generateJobListing(input: GenerateJobListingInput): Promise<GenerateJobListingOutput> {
  return generateJobListingFlow(input);
}

const prompt = ai.definePrompt({
  name: 'generateJobListingPrompt',
  input: {schema: GenerateJobListingInputSchema},
  output: {schema: GenerateJobListingOutputSchema},
  prompt: `You are an expert recruiter specializing in creating job listings.

  You will use this job description to generate a job listing.

  Job Description: {{{jobDescription}}}
  `,
});

const generateJobListingFlow = ai.defineFlow(
  {
    name: 'generateJobListingFlow',
    inputSchema: GenerateJobListingInputSchema,
    outputSchema: GenerateJobListingOutputSchema,
  },
  async input => {
    const {output} = await prompt(input);
    return output!;
  }
);
