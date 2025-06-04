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
  prompt: `You are an expert recruiter specializing in creating compelling and detailed job listings that attract top talent.

You will use the provided job description to generate a comprehensive job listing. This listing should follow best practices observed in successful online job postings.

Ensure the job listing includes, but is not limited to, the following sections:
- **Job Title:** Clear and concise.
- **Company Overview:** A brief, engaging description of the company and its mission/culture.
- **Job Summary:** An overview of the role and its purpose within the company.
- **Key Responsibilities:** A detailed list of primary duties and tasks.
- **Required Qualifications:** Essential skills, experience, and education.
- **Preferred Qualifications:** Desirable, but not mandatory, skills and experience.
- **Benefits:** Highlight key benefits and perks offered.
- **Call to Action:** How to apply.

The tone should be professional, engaging, and inclusive.

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

