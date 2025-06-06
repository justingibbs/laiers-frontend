
"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
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
import { generateJobListing } from '@/ai/flows/generate-job-listing';
import { createSkillsSurvey } from '@/ai/flows/create-skills-survey';
import type { CreateSkillsSurveyOutput } from '@/ai/flows/create-skills-survey';
import { useAppStore } from '@/lib/store';
import type { Job as JobType } from '@/lib/types';
import SkillIcon from '@/components/SkillIcon';
import { CheckCircle, ClipboardCopy, Lightbulb, ListChecks, ArrowRight } from 'lucide-react';
import ClientOnly from '@/components/ClientOnly';

const jobDescriptionSchema = z.object({
  jobTitle: z.string().min(3, { message: "Job title must be at least 3 characters." }),
  jobDescription: z.string().min(50, { message: "Job description must be at least 50 characters." }),
});
type JobDescriptionFormData = z.infer<typeof jobDescriptionSchema>;

export default function CreateJobPage() {
  const [isLoadingListing, setIsLoadingListing] = useState(false);
  const [isLoadingSurvey, setIsLoadingSurvey] = useState(false);
  const [generatedListing, setGeneratedListing] = useState<string | null>(null);
  const [surveyData, setSurveyData] = useState<CreateSkillsSurveyOutput | null>(null);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [_jobTitle, setJobTitle] = useState<string>(""); 
  const [shareableSurveyLink, setShareableSurveyLink] = useState<string>("");

  const router = useRouter();
  const { toast } = useToast();
  const createJobInStore = useAppStore((state) => state.createJob);
  const updateJobInStore = useAppStore((state) => state.updateJob);
  const storeIsLoading = useAppStore((state) => state.isLoading);
  const storeError = useAppStore((state) => state.error);

  const form = useForm<JobDescriptionFormData>({
    resolver: zodResolver(jobDescriptionSchema),
    defaultValues: { jobTitle: "", jobDescription: "" },
  });

  useEffect(() => {
    if (currentJobId && surveyData && typeof window !== 'undefined') {
      setShareableSurveyLink(`${window.location.origin}/job/${currentJobId}/take-survey`);
    } else {
      setShareableSurveyLink("");
    }
  }, [currentJobId, surveyData]);

  const handleGenerateListing: SubmitHandler<JobDescriptionFormData> = async (data) => {
    setIsLoadingListing(true);
    setGeneratedListing(null);
    setSurveyData(null);
    setCurrentJobId(null);
    setJobTitle(data.jobTitle);

    try {
      const result = await generateJobListing({ jobDescription: data.jobDescription });
      setGeneratedListing(result.jobListing);
      
      const newJobData = {
        title: data.jobTitle,
        descriptionInput: data.jobDescription,
        generatedListingText: result.jobListing,
      };
      const newJobId = await createJobInStore(newJobData);

      if (newJobId) {
        setCurrentJobId(newJobId);
        toast({ title: "Success", description: "Job listing generated and saved!" });
      } else {
        // Error should have been set in the store
        const currentStoreError = useAppStore.getState().error;
        toast({ 
          variant: "destructive", 
          title: "Error Saving Job", 
          description: currentStoreError || "Failed to save job listing. No ID was returned." 
        });
      }
    } catch (error) {
      console.error("Error generating or saving job listing:", error);
      toast({ 
        variant: "destructive", 
        title: "Operation Failed", 
        description: (error as Error).message || "An unexpected error occurred." 
      });
    }
    setIsLoadingListing(false);
  };

  const handleCreateSurvey = async () => {
    if (!generatedListing || !currentJobId) {
      toast({variant: "destructive", title: "Missing Data", description: "Cannot create survey without a generated listing and job ID."});
      return;
    }
    setIsLoadingSurvey(true);
    try {
      const result = await createSkillsSurvey({ jobListing: generatedListing });
      setSurveyData(result);
      await updateJobInStore(currentJobId, { survey: result });
      toast({ title: "Success", description: "Skills survey created and saved!" });
    } catch (error) {
      console.error("Error creating skills survey:", error);
      toast({ 
        variant: "destructive", 
        title: "Survey Creation Failed", 
        description: (error as Error).message || "Failed to create skills survey." 
      });
    }
    setIsLoadingSurvey(false);
  };

  const handleFinalize = () => {
    if (!currentJobId) {
        toast({variant: "destructive", title: "Error", description: "No job ID available to finalize."});
        return;
    };
    router.push(`/job/${currentJobId}/applicants`);
  };
  
  const copyToClipboard = (text: string) => {
    if (!text || typeof navigator === 'undefined' || !navigator.clipboard) {
        toast({variant: "destructive", title: "Error", description: "Clipboard not available."});
        return;
    }
    navigator.clipboard.writeText(text).then(() => {
      toast({ title: "Copied!", description: "Link copied to clipboard." });
    }).catch(err => {
      console.error("Failed to copy to clipboard:", err);
      toast({ variant: "destructive", title: "Error", description: "Failed to copy link." });
    });
  };

  const pageLoading = isLoadingListing || isLoadingSurvey || storeIsLoading;

  return (
    <ClientOnly>
      <div className="space-y-8 max-w-4xl mx-auto">
        <h1 className="text-3xl font-headline font-bold text-center">Create New Job & Survey</h1>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Lightbulb className="text-primary"/> Step 1: Define the Role</CardTitle>
            <CardDescription>Provide a title and detailed description for the job you want to fill.</CardDescription>
          </CardHeader>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(handleGenerateListing)}>
              <CardContent className="space-y-4">
                <FormField
                  control={form.control}
                  name="jobTitle"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Job Title</FormLabel>
                      <FormControl>
                        <Input placeholder="e.g., Senior Software Engineer" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="jobDescription"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Job Description</FormLabel>
                      <FormControl>
                        <Textarea placeholder="Describe the responsibilities, qualifications, and company culture..." {...field} rows={8} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </CardContent>
              <CardFooter>
                <Button type="submit" disabled={pageLoading} className="w-full sm:w-auto">
                  {isLoadingListing ? <LoadingSpinner /> : "Generate Job Listing"}
                  {!isLoadingListing && <ArrowRight className="ml-2 h-4 w-4" />}
                </Button>
              </CardFooter>
            </form>
          </Form>
        </Card>

        {generatedListing && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><CheckCircle className="text-green-500"/> Generated Job Listing</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose prose-sm max-w-none p-4 border rounded-md bg-secondary/30 max-h-96 overflow-y-auto">
                <pre className="whitespace-pre-wrap font-body">{generatedListing}</pre>
              </div>
            </CardContent>
            <CardFooter>
              <Button onClick={handleCreateSurvey} disabled={pageLoading || !currentJobId} className="w-full sm:w-auto">
                  {isLoadingSurvey ? <LoadingSpinner /> : "Create Skills Survey"}
                  {!isLoadingSurvey && <ArrowRight className="ml-2 h-4 w-4" />}
                </Button>
            </CardFooter>
          </Card>
        )}

        {surveyData && currentJobId && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><ListChecks className="text-primary"/> Step 2: Skills Survey Created</CardTitle>
              <CardDescription>Based on the job listing, we've identified key soft skills and generated survey questions. This survey is now saved.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h3 className="font-semibold mb-2 text-lg">Top 3 Soft Skills Identified:</h3>
                <ul className="space-y-1 list-inside">
                  {surveyData.topSkills.map((skill) => (
                    <li key={skill} className="flex items-center gap-2 p-2 bg-secondary/30 rounded-md">
                      <SkillIcon skill={skill} className="h-5 w-5 text-accent" />
                      <span>{skill}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="font-semibold mb-2 text-lg">Survey Questions ({surveyData.surveyQuestions.length}):</h3>
                <div className="space-y-2 max-h-96 overflow-y-auto p-4 border rounded-md bg-secondary/30">
                  {surveyData.surveyQuestions.map((q, index) => (
                    <p key={index} className="text-sm p-2 border-b border-border/50 last:border-b-0">
                      {index + 1}. {q}
                    </p>
                  ))}
                </div>
              </div>
              <div className="mt-4">
                  <h3 className="font-semibold mb-2 text-lg">Shareable Survey Link:</h3>
                  <div className="flex items-center gap-2">
                    <Input
                      readOnly
                      value={shareableSurveyLink}
                      className="bg-muted"
                      disabled={!shareableSurveyLink}
                    />
                    <Button variant="outline" size="icon" onClick={() => copyToClipboard(shareableSurveyLink)} disabled={!shareableSurveyLink}>
                      <ClipboardCopy className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
            </CardContent>
            <CardFooter>
              <Button onClick={handleFinalize} className="w-full sm:w-auto bg-accent hover:bg-accent/90" disabled={pageLoading}>
                View Applicant Dashboard <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </CardFooter>
          </Card>
        )}
      </div>
    </ClientOnly>
  );
}

