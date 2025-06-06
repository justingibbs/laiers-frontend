
"use client";

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useForm, type SubmitHandler } from 'react-hook-form';
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
import { Send, CheckCircle, User, AlertTriangle } from 'lucide-react';
import ClientOnly from '@/components/ClientOnly';

const createSurveySchema = (questions: string[]) => {
  const schemaFields: Record<string, z.ZodString> = {
    applicantName: z.string().min(2, { message: "Name must be at least 2 characters." }),
  };
  questions.forEach((_, index) => {
    schemaFields[`answer${index}`] = z.string().min(10, { message: "Answer must be at least 10 characters." });
  });
  return z.object(schemaFields);
};

type SurveyFormData = Record<string, string> & { applicantName: string };


export default function TakeSurveyPage() {
  const params = useParams();
  const jobId = params.jobId as string;
  const router = useRouter();
  const { toast } = useToast();

  const { getJob: getJobFromStore, addApplicant, updateApplicant } = useAppStore();
  const [job, setJob] = useState<Job | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [submissionSummary, setSubmissionSummary] = useState<string | null>(null);
  const [isLoadingJob, setIsLoadingJob] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  
  const [surveyQuestions, setSurveyQuestions] = useState<string[]>([]);
  const [isStoreHydrated, setIsStoreHydrated] = useState(false);

  const form = useForm<SurveyFormData>({
    resolver: zodResolver(createSurveySchema(surveyQuestions)),
    defaultValues: { applicantName: "" }, 
  });

  useEffect(() => {
    // Handle Zustand store hydration
    // Initialize with current status, then set up listener
    setIsStoreHydrated(useAppStore.persist.hasHydrated());

    const unsub = useAppStore.persist.onFinishHydration(() => {
      setIsStoreHydrated(true);
    });

    // Fallback if onFinishHydration was missed (e.g. store already hydrated before listener attached)
    // This ensures we capture the state even if the event fired before this effect ran.
    if (useAppStore.persist.hasHydrated() && !isStoreHydrated) {
        setIsStoreHydrated(true);
    }
    
    return () => {
      unsub(); // Cleanup subscription
    };
  }, []); // Runs once on mount


  useEffect(() => {
    // Fetch job data only after store is hydrated
    if (!isStoreHydrated) {
      setIsLoadingJob(true); 
      return;
    }

    setIsLoadingJob(true);
    const jobData = getJobFromStore(jobId);
    if (jobData) {
      setJob(jobData);
      const questions = jobData.survey?.questions || [];
      setSurveyQuestions(questions);
      form.reset(
        questions.reduce((acc, _, index) => ({ ...acc, [`answer${index}`]: "" }), { applicantName: form.getValues("applicantName") || "" })
      );
      setErrorMessage(null);
    } else {
      setJob(null);
      setSurveyQuestions([]);
      setErrorMessage("Job not found or survey is not available for this job.");
    }
    setIsLoadingJob(false);
  }, [jobId, getJobFromStore, isStoreHydrated, form]); // Added form to dependencies for reset

  useEffect(() => {
    // Handle error messages and redirection
    if (!isStoreHydrated) return; 

    if (errorMessage && !isLoadingJob && !job) {
      toast({ variant: "destructive", title: "Error", description: errorMessage });
      router.push('/');
    }
  }, [errorMessage, isLoadingJob, job, router, toast, isStoreHydrated]);


  const handleSubmitSurvey: SubmitHandler<SurveyFormData> = async (data) => {
    if (!job || !job.survey) {
      toast({ variant: "destructive", title: "Error", description: "Survey details are missing." });
      return;
    }
    setIsSubmitting(true);

    const currentResponses = job.survey.questions.map((question, index) => ({
      question,
      answer: data[`answer${index}`] as string,
    }));

    const applicantId = `app-${Date.now()}`;
    const newApplicant: Applicant = {
      id: applicantId,
      name: data.applicantName,
      jobId: job.id,
      responses: currentResponses,
      submittedAt: Date.now(),
    };
    addApplicant(job.id, newApplicant);

    try {
      const analysisInput = {
        jobListing: job.generatedListingText || job.descriptionInput,
        softSkills: job.survey.topSkills,
        responses: currentResponses,
      };
      const analysisResult = await analyzeSurveyResponses(analysisInput);
      updateApplicant(job.id, applicantId, { analysisOutput: analysisResult });
      
      const surveyResponsesMap: Record<string, string> = {};
      currentResponses.forEach(r => { surveyResponsesMap[r.question] = r.answer; });
      
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
    setIsSubmitting(false);
  };

  if (!isStoreHydrated || isLoadingJob) {
    return (
      <ClientOnly> 
        <div className="flex justify-center items-center min-h-[calc(100vh-200px)]">
          <LoadingSpinner size={48} />
        </div>
      </ClientOnly>
    );
  }

  if (errorMessage && !job) {
     return (
      <ClientOnly>
        <div className="flex flex-col justify-center items-center min-h-[calc(100vh-200px)] text-center p-4">
          <AlertTriangle className="h-12 w-12 text-destructive mb-4" />
          <h1 className="text-2xl font-bold mb-2">Survey Not Available</h1>
          <p className="text-muted-foreground mb-4">{errorMessage}</p>
          <Button onClick={() => router.push('/')} className="mt-4">Back to Home</Button>
        </div>
      </ClientOnly>
    );
  }
  
  if (!job?.survey?.questions || surveyQuestions.length === 0) {
     return (
      <ClientOnly>
        <div className="flex flex-col justify-center items-center min-h-[calc(100vh-200px)] text-center p-4">
          <AlertTriangle className="h-12 w-12 text-muted-foreground mb-4" />
          <h1 className="text-2xl font-bold mb-2">Survey Not Configured</h1>
          <p className="text-muted-foreground mb-4">This job does not have an active survey or questions are missing.</p>
          <Button onClick={() => router.push('/')} className="mt-4">Back to Home</Button>
        </div>
      </ClientOnly>
    );
  }

  if (isSubmitted) {
    return (
      <ClientOnly>
        <Card className="max-w-2xl mx-auto my-8">
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
      </ClientOnly>
    );
  }

  return (
    <ClientOnly>
      <div className="max-w-2xl mx-auto space-y-8 py-8">
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl font-headline">Skills Survey: {job.title}</CardTitle>
            <CardDescription>Please answer the following questions thoughtfully. Your responses will help us understand your approach to various situations.</CardDescription>
            {job.survey?.topSkills && (
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
            )}
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
                    name={`answer${index}`}
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
                <Button type="submit" disabled={isSubmitting} className="w-full">
                  {isSubmitting ? <LoadingSpinner /> : "Submit Responses"}
                  {!isSubmitting && <Send className="ml-2 h-4 w-4" />}
                </Button>
              </CardFooter>
            </form>
          </Form>
        </Card>
      </div>
    </ClientOnly>
  );
}
