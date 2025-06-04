import { config } from 'dotenv';
config();

import '@/ai/flows/create-skills-survey.ts';
import '@/ai/flows/analyze-survey-responses.ts';
import '@/ai/flows/generate-job-listing.ts';
import '@/ai/flows/summarize-survey-responses.ts';