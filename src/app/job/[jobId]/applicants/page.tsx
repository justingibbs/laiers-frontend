
"use client";

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import LoadingSpinner from '@/components/LoadingSpinner';
import { useToast } from '@/hooks/use-toast';
import { useAppStore } from '@/lib/store';
import type { Job, Applicant } from '@/lib/types';
import { Users, TrendingUp, ClipboardCopy, AlertTriangle, Eye } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import FormattedDate from '@/components/FormattedDate';

export default function ApplicantDashboardPage() {
  const params = useParams();
  const jobId = params.jobId as string;
  const router = useRouter();
  const { toast } = useToast();

  const getJobFromStore = useAppStore((state) => state.getJob);
  const [job, setJob] = useState<Job | null>(null);
  const [sortedApplicants, setSortedApplicants] = useState<Applicant[]>([]);
  const [mounted, setMounted] = useState(false);
  const [surveyLink, setSurveyLink] = useState<string>("");

  useEffect(() => {
    setMounted(true); 
    const jobData = getJobFromStore(jobId);
    if (jobData) {
      setJob(jobData);
      const applicantsWithScores = jobData.applicants.filter(app => app.overallScoreData);
      const sorted = [...applicantsWithScores].sort((a, b) => (b.overallScoreData?.overallScore || 0) - (a.overallScoreData?.overallScore || 0));
      setSortedApplicants(sorted);
    } else {
      if (mounted) { // Only toast and redirect if mounted, to avoid issues during SSR or initial client render
        toast({ variant: "destructive", title: "Error", description: "Job not found." });
        router.push('/');
      }
    }
  }, [jobId, getJobFromStore, mounted, router, toast]);

  useEffect(() => {
    if (jobId && typeof window !== 'undefined') {
      setSurveyLink(`${window.location.origin}/job/${jobId}/take-survey`);
    }
  }, [jobId]);

  const copyToClipboard = (text: string) => {
    if (!text) return;
    navigator.clipboard.writeText(text).then(() => {
      toast({ title: "Copied!", description: "Link copied to clipboard." });
    }).catch(err => {
      toast({ variant: "destructive", title: "Error", description: "Failed to copy link." });
    });
  };

  if (!mounted) {
    return (
      <div className="flex justify-center items-center min-h-[calc(100vh-200px)]">
        <LoadingSpinner size={48} />
      </div>
    );
  }
  
  if (!job) {
    return (
      <div className="flex flex-col justify-center items-center min-h-[calc(100vh-200px)]">
        <AlertTriangle className="h-12 w-12 text-destructive mb-4" />
        <h2 className="text-xl font-semibold">Job Not Found</h2>
        <p className="text-muted-foreground">The requested job could not be loaded.</p>
        <Button onClick={() => router.push('/')} className="mt-4">Back to Home</Button>
      </div>
    );
  }
  
  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-headline font-bold">{job.title} - Applicant Dashboard</h1>
          <p className="text-muted-foreground">Review applicants based on their survey responses and AI-generated scores.</p>
        </div>
         <Button asChild variant="outline">
            <Link href="/">Back to Jobs List</Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Share Survey Link</CardTitle>
          <CardDescription>Provide this link to potential applicants to take the skills survey.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            <Input
              readOnly
              value={surveyLink}
              className="bg-muted flex-grow"
              disabled={!surveyLink}
            />
            <Button variant="outline" size="icon" onClick={() => copyToClipboard(surveyLink)} disabled={!surveyLink}>
              <ClipboardCopy className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>


      {job.applicants.filter(app => app.overallScoreData).length === 0 ? (
        <Card className="text-center py-12">
           <CardHeader>
            <Users className="mx-auto h-16 w-16 text-muted-foreground mb-4" />
            <CardTitle className="text-2xl">No Analyzed Applicants Yet</CardTitle>
            <CardDescription>
              Share the survey link. Responses with completed AI analysis will appear here.
            </CardDescription>
          </CardHeader>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><TrendingUp className="text-primary"/> Applicant Overview</CardTitle>
            <CardDescription>Applicants are sorted by their overall score (highest first).</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Rank</TableHead>
                  <TableHead>Applicant Name</TableHead>
                  <TableHead className="text-right">Overall Score</TableHead>
                  <TableHead className="text-center">Submitted</TableHead>
                  <TableHead className="text-center">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sortedApplicants.map((applicant, index) => (
                  <TableRow key={applicant.id}>
                    <TableCell>{index + 1}</TableCell>
                    <TableCell className="font-medium">{applicant.name}</TableCell>
                    <TableCell className="text-right">
                      <Badge variant={ (applicant.overallScoreData?.overallScore || 0) >= 75 ? "default" : (applicant.overallScoreData?.overallScore || 0) >= 50 ? "secondary" : "destructive" } 
                             className="text-sm px-3 py-1">
                        {applicant.overallScoreData?.overallScore.toFixed(0) || 'N/A'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-center">
                       <FormattedDate timestamp={applicant.submittedAt} className="text-xs text-muted-foreground" />
                    </TableCell>
                    <TableCell className="text-center">
                      <Button asChild variant="ghost" size="sm">
                        <Link href={`/job/${jobId}/applicant/${applicant.id}`}>
                          <Eye className="mr-1 h-4 w-4" /> View Details
                        </Link>
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
       {job.applicants.length > sortedApplicants.length && (
        <Card className="border-yellow-500 border-2">
            <CardHeader>
                <CardTitle className="flex items-center gap-2 text-yellow-700">
                    <AlertTriangle className="h-5 w-5" /> Pending Analysis
                </CardTitle>
                <CardDescription>
                    {job.applicants.length - sortedApplicants.length} applicant(s) have submitted responses but are still being processed or encountered an error during AI analysis. They will appear in the main list once analysis is complete.
                </CardDescription>
            </CardHeader>
        </Card>
       )}
    </div>
  );
}
