"use client";

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useForm, type SubmitHandler, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import LoadingSpinner from '@/components/LoadingSpinner';
import { useToast } from '@/hooks/use-toast';
import { useAppStore } from '@/lib/store';
import type { Job, Applicant } from '@/lib/types';
import { analyzeSurveyResponses } from '@/ai/flows/analyze-survey-responses';
import { summarizeSurveyResponses } from '@/ai/flows/summarize-survey-responses';
import SkillIcon from '@/components/SkillIcon';
import { Send, CheckCircle, User } from 'lucide-react';

// Dynamically create schema based on questions
const createSurveySchema = (questions: string[]) => {
  const schemaFields: Record<string, z.ZodString> = {
    applicantName: z.string().min(2, { message: "Name must be at least 2 characters." }),
  };
  questions.forEach((_, index) => {
    schemaFields[`answer${index}`] = z.string().min(10, { message: "Answer must be at least 10 characters." });
  });
  return z.object(schemaFields);
};

type SurveyFormData = z.infer<ReturnType<typeof createSurveySchema>>;

export default function TakeSurveyPage() {
  const params = useParams();
  const jobId = params.jobId as string;
  const router = useRouter();
  const { toast } = useToast();

  const { getJob, addApplicant, updateApplicant } = useAppStore();
  const [job, setJob] = useState<Job | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [submissionSummary, setSubmissionSummary] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const jobData = getJob(jobId);
    if (jobData) {
      setJob(jobData);
    } else {
      toast({ variant: "destructive", title: "Error", description: "Job not found." });
      router.push('/');
    }
  }, [jobId, getJob, toast, router]);
  
  const surveyQuestions = job?.survey?.questions || [];
  const surveySchema = createSurveySchema(surveyQuestions);

  const form = useForm<SurveyFormData>({
    resolver: zodResolver(surveySchema),
    defaultValues: { applicantName: "" }, // Answers will be undefined initially
  });

  const handleSubmitSurvey: SubmitHandler<SurveyFormData> = async (data) => {
    if (!job || !job.survey) return;
    setIsLoading(true);

    const responses = surveyQuestions.map((question, index) => ({
      question,
      answer: data[`answer${index}` as keyof SurveyFormData] as string,
    }));

    const applicantId = `app-${Date.now()}`;
    const newApplicant: Applicant = {
      id: applicantId,
      name: data.applicantName,
      jobId: job.id,
      responses,
      submittedAt: Date.now(),
    };
    addApplicant(job.id, newApplicant);

    try {
      // AI Analysis
      const analysisInput = {
        jobListing: job.generatedListingText || job.descriptionInput,
        softSkills: job.survey.topSkills,
        responses: responses,
      };
      const analysisResult = await analyzeSurveyResponses(analysisInput);
      updateApplicant(job.id, applicantId, { analysisOutput: analysisResult });
      
      // AI Summary
      const surveyResponsesMap: Record<string, string> = {};
      responses.forEach(r => { surveyResponsesMap[r.question] = r.answer; });
      
      const summaryInput = {
        jobListing: job.generatedListingText || job.descriptionInput,
        surveyResponses: surveyResponsesMap,
        softSkills: job.survey.topSkills,
      };
      const summaryResult = await summarizeSurveyResponses(summaryInput);
      updateApplicant(job.id, applicantId, { overallScoreData: summaryResult });

      setSubmissionSummary(summaryResult.summary);
      setIsSubmitted(true);
      toast({ title: "Success", description: "Survey submitted successfully!" });

    } catch (error) {
      console.error("Error processing survey:", error);
      toast({ variant: "destructive", title: "Error", description: "Failed to process survey responses." });
    }
    setIsLoading(false);
  };

  if (!mounted || !job) {
    return <div className="flex justify-center items-center min-h-[calc(100vh-200px)]"><LoadingSpinner size={48} /></div>;
  }
  if (!job.survey) {
     return (
      <div className="text-center py-10">
        <h1 className="text-2xl font-bold mb-4">Survey Not Available</h1>
        <p className="text-muted-foreground">This job does not have an active survey.</p>
        <Button onClick={() => router.push('/')} className="mt-4">Back to Home</Button>
      </div>
    );
  }


  if (isSubmitted) {
    return (
      <Card className="max-w-2xl mx-auto">
        <CardHeader className="text-center">
          <CheckCircle className="mx-auto h-16 w-16 text-green-500 mb-4" />
          <CardTitle className="text-2xl">Thank You for Your Submission!</CardTitle>
          <CardDescription>Your responses have been recorded.</CardDescription>
        </CardHeader>
        {submissionSummary && (
          <CardContent>
            <h3 className="font-semibold mb-2 text-lg">Your Quick Summary:</h3>
            <p className="text-sm p-4 border rounded-md bg-secondary/30 whitespace-pre-line">{submissionSummary}</p>
          </CardContent>
        )}
        <CardFooter className="flex justify-center">
          <Button onClick={() => router.push('/')}>Return to Homepage</Button>
        </CardFooter>
      </Card>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl font-headline">Skills Survey: {job.title}</CardTitle>
          <CardDescription>Please answer the following questions thoughtfully. Your responses will help us understand your approach to various situations.</CardDescription>
          <div className="pt-2">
            <h3 className="text-sm font-semibold">Key Skills Assessed:</h3>
            <div className="flex flex-wrap gap-2 mt-1">
              {job.survey.topSkills.map(skill => (
                <span key={skill} className="flex items-center gap-1 text-xs px-2 py-1 bg-primary/10 text-primary rounded-full">
                  <SkillIcon skill={skill} className="h-3 w-3" />
                  {skill}
                </span>
              ))}
            </div>
          </div>
        </CardHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmitSurvey)}>
            <CardContent className="space-y-6">
              <FormField
                control={form.control}
                name="applicantName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-base">Your Name</FormLabel>
                    <FormControl>
                      <div className="flex items-center gap-2">
                        <User className="h-5 w-5 text-muted-foreground" />
                        <Input placeholder="Enter your full name" {...field} />
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              {surveyQuestions.map((question, index) => (
                <FormField
                  key={index}
                  control={form.control}
                  name={`answer${index}` as keyof SurveyFormData}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-base">Question {index + 1}: {question}</FormLabel>
                      <FormControl>
                        <Textarea placeholder="Your detailed answer..." {...field} rows={5} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              ))}
            </CardContent>
            <CardFooter>
              <Button type="submit" disabled={isLoading} className="w-full">
                {isLoading ? <LoadingSpinner /> : "Submit Responses"}
                {!isLoading && <Send className="ml-2 h-4 w-4" />}
              </Button>
            </CardFooter>
          </form>
        </Form>
      </Card>
    </div>
  );
}
