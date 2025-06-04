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
  prompt: `You are an expert recruiter specializing in creating compelling, detailed, and highly polished job listings optimized for platforms like LinkedIn and Indeed. Your goal is to attract top talent.

You will use the provided job description to generate a comprehensive and professional job listing. This listing should follow best practices observed in successful online job postings, ensuring it is well-structured, easy to read, and engaging.

Ensure the job listing includes, but is not limited to, the following sections, formatted clearly (e.g., using markdown for headings and bullet points where appropriate):
- **Job Title:** Clear, concise, and industry-standard.
- **Company Overview:** A brief, engaging description of the company, its mission, values, and culture. Highlight what makes it a great place to work.
- **Job Summary:** An overview of the role and its purpose within the company, emphasizing its impact.
- **Key Responsibilities:** A detailed list of primary duties and tasks, using action verbs.
- **Required Qualifications:** Essential skills, experience (years, specific technologies), and education. Be specific.
- **Preferred Qualifications:** Desirable, but not mandatory, skills, experience, or certifications that would make a candidate stand out.
- **What We Offer / Benefits:** Highlight key benefits, perks, salary range (if appropriate/legal), and opportunities for growth and development.
- **Equal Opportunity Employer Statement:** (If applicable/desired)
- **Call to Action:** Clear instructions on how to apply, including any specific requirements for the application (e.g., cover letter, portfolio). Encourage qualified candidates to apply.

The tone should be professional, inviting, inclusive, and enthusiastic. Avoid jargon where possible, or explain it if necessary. The final output should be ready to be copied and pasted directly onto a job board.

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
