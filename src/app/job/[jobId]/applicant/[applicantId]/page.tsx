
"use client";

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import LoadingSpinner from '@/components/LoadingSpinner';
import { useToast } from '@/hooks/use-toast';
import { useAppStore } from '@/lib/store';
import type { Job, Applicant } from '@/lib/types';
import SkillIcon from '@/components/SkillIcon';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { BarChart, Brain, FileText, MessageSquare, Users, ShieldCheck, Lightbulb, Repeat, Sparkles, ChevronLeft, Star, AlertTriangle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';

export default function ApplicantDetailPage() {
  const params = useParams();
  const jobId = params.jobId as string;
  const applicantId = params.applicantId as string;
  const router = useRouter();
  const { toast } = useToast();

  const { getJob, getApplicant } = useAppStore();
  const [job, setJob] = useState<Job | null>(null);
  const [applicant, setApplicant] = useState<Applicant | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const jobData = getJob(jobId);
    const applicantData = getApplicant(jobId, applicantId);

    if (jobData) setJob(jobData);
    if (applicantData) setApplicant(applicantData);

    if (mounted) { // Only show toast/redirect if component is truly mounted and data is missing
      if (!jobData) {
        toast({ variant: "destructive", title: "Error", description: "Job not found." });
        router.push(jobId ? `/job/${jobId}/applicants` : '/');
      } else if (!applicantData) {
        toast({ variant: "destructive", title: "Error", description: "Applicant not found." });
        router.push(`/job/${jobId}/applicants`);
      }
    }
  }, [jobId, applicantId, getJob, getApplicant, mounted, toast, router]);


  if (!mounted) {
    return (
      <div className="flex justify-center items-center min-h-[calc(100vh-200px)]">
        <LoadingSpinner size={48} />
      </div>
    );
  }

  if (!job || !applicant) {
     return (
      <div className="flex flex-col justify-center items-center min-h-[calc(100vh-200px)]">
        <AlertTriangle className="h-12 w-12 text-destructive mb-4" />
        <h2 className="text-xl font-semibold">Applicant or Job Data Not Found</h2>
        <p className="text-muted-foreground">The requested details could not be loaded.</p>
        <Button onClick={() => router.push(jobId ? `/job/${jobId}/applicants` : '/')} className="mt-4">
          Back to Dashboard
        </Button>
      </div>
    );
  }

  const renderScoreBar = (skillName: string, score: number) => (
    <div key={skillName} className="mb-3">
      <div className="flex justify-between items-center mb-1">
        <span className="text-sm font-medium flex items-center">
          <SkillIcon skill={skillName} className="h-4 w-4 mr-2 text-primary" />
          {skillName}
        </span>
        <span className="text-sm font-semibold text-primary">{score.toFixed(0)}/100</span>
      </div>
      <Progress value={score} className="h-2" />
    </div>
  );

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      <Button asChild variant="outline" size="sm" className="mb-4">
        <Link href={`/job/${jobId}/applicants`}>
          <ChevronLeft className="mr-1 h-4 w-4" /> Back to Applicant Dashboard
        </Link>
      </Button>

      <Card>
        <CardHeader>
          <CardTitle className="text-3xl font-headline">{applicant.name}</CardTitle>
          <CardDescription>Detailed Review for Job: <span className="font-semibold">{job.title}</span></CardDescription>
          {applicant.overallScoreData && (
            <div className="flex items-center gap-2 pt-2">
              <Star className="h-6 w-6 text-yellow-400 fill-yellow-400" />
              <span className="text-xl font-bold text-primary">
                Overall Score: {applicant.overallScoreData.overallScore.toFixed(0)}/100
              </span>
            </div>
          )}
        </CardHeader>
      </Card>

      {/* AI Analysis & Scores */}
      {applicant.analysisOutput && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><BarChart className="text-primary"/> AI-Powered Insights</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {applicant.overallScoreData && (
              <div>
                <h3 className="font-semibold mb-2 text-lg">Overall Summary:</h3>
                <p className="text-sm p-4 border rounded-md bg-secondary/30 whitespace-pre-line">{applicant.overallScoreData.summary}</p>
              </div>
            )}
            
            <div>
              <h3 className="font-semibold mb-2 text-lg">Soft Skill Scores:</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2">
                {Object.entries(applicant.analysisOutput.scores).map(([skill, score]) =>
                  renderScoreBar(skill, score)
                )}
              </div>
            </div>

            {applicant.analysisOutput.analysis && (
              <div>
                <h3 className="font-semibold mb-2 text-lg">Detailed Analysis:</h3>
                <p className="text-sm p-4 border rounded-md bg-secondary/30 whitespace-pre-line">{applicant.analysisOutput.analysis}</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}
      
      {!applicant.analysisOutput && (
         <Card className="border-orange-500 border-2">
            <CardHeader>
                <CardTitle className="flex items-center gap-2 text-orange-700">
                    <Brain className="h-5 w-5" /> Analysis Pending or Failed
                </CardTitle>
                <CardDescription>
                    The detailed AI analysis for this applicant is not yet available. It might still be processing or an error occurred.
                </CardDescription>
            </CardHeader>
        </Card>
      )}


      {/* Survey Responses */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><MessageSquare className="text-primary"/> Survey Responses</CardTitle>
        </CardHeader>
        <CardContent>
          <Accordion type="single" collapsible className="w-full">
            {applicant.responses.map((response, index) => (
              <AccordionItem value={`item-${index}`} key={index}>
                <AccordionTrigger className="text-left hover:no-underline">
                  <span className="font-medium">Q{index + 1}:</span> {response.question}
                </AccordionTrigger>
                <AccordionContent className="p-4 bg-secondary/30 rounded-md whitespace-pre-line">
                  {response.answer}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </CardContent>
      </Card>

      {/* Job Listing Context */}
      {job.generatedListingText && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><FileText className="text-primary"/> Original Job Listing (for context)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm max-w-none p-4 border rounded-md bg-secondary/30 max-h-72 overflow-y-auto">
              <pre className="whitespace-pre-wrap font-body">{job.generatedListingText}</pre>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
