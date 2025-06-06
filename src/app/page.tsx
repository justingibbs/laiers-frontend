
"use client";

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { useAppStore } from '@/lib/store';
import { useEffect, useState } from 'react';
import type { Job } from '@/lib/types';
import { PlusCircle, Users, FileText, Trash2, AlertTriangle } from 'lucide-react';
import LoadingSpinner from '@/components/LoadingSpinner';
import FormattedDate from '@/components/FormattedDate';
import ClientOnly from '@/components/ClientOnly';
import { useToast } from '@/hooks/use-toast';

export default function HomePage() {
  const { 
    jobs, 
    isLoading: isLoadingJobs, 
    error: jobsError, 
    fetchJobs, 
    deleteJob 
  } = useAppStore(state => ({
    jobs: state.getAllJobsFromCache(), // Use cache getter for display
    isLoading: state.isLoading,
    error: state.error,
    fetchJobs: state.fetchJobs,
    deleteJob: state.deleteJob,
  }));
  
  const [jobToDelete, setJobToDelete] = useState<Job | null>(null);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  const openDeleteDialog = (job: Job) => {
    setJobToDelete(job);
    setIsDeleteDialogOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (jobToDelete) {
      await deleteJob(jobToDelete.id);
      // Zustand store should update the jobs list automatically after deleteJob resolves
      // and fetchJobs is called or local cache is updated by deleteJob.
      // Forcing a re-fetch here, or relying on deleteJob to update the cache is an option.
      // The current store implementation optimistically removes, so UI should update.
      toast({
        title: "Job Deleted",
        description: `The job "${jobToDelete.title}" has been successfully deleted.`,
      });
      setIsDeleteDialogOpen(false);
      setJobToDelete(null);
    }
  };
  
  if (isLoadingJobs && jobs.length === 0) { // Show loader only on initial load
    return (
      <div className="flex justify-center items-center min-h-[calc(100vh-200px)]">
        <LoadingSpinner size={48} />
      </div>
    );
  }

  if (jobsError) {
    return (
      <ClientOnly>
        <div className="flex flex-col justify-center items-center min-h-[calc(100vh-200px)] text-center p-4">
          <AlertTriangle className="h-12 w-12 text-destructive mb-4" />
          <h1 className="text-2xl font-bold mb-2">Error Loading Jobs</h1>
          <p className="text-muted-foreground mb-4">{jobsError}</p>
          <Button onClick={fetchJobs}>Try Again</Button>
        </div>
      </ClientOnly>
    );
  }

  return (
    <ClientOnly>
      <div className="space-y-8">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h1 className="text-3xl font-headline font-bold">Job Dashboard</h1>
          <Button asChild variant="default" size="lg">
            <Link href="/create-job">
              <PlusCircle className="mr-2 h-5 w-5" /> Create New Job & Survey
            </Link>
          </Button>
        </div>

        {jobs.length === 0 && !isLoadingJobs ? (
          <Card className="text-center py-12">
            <CardHeader>
              <FileText className="mx-auto h-16 w-16 text-muted-foreground mb-4" />
              <CardTitle className="text-2xl">No Jobs Created Yet</CardTitle>
              <CardDescription>
                Start by creating a new job listing and skills survey.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button asChild className="mt-4" variant="default">
                <Link href="/create-job">
                  <PlusCircle className="mr-2 h-4 w-4" /> Create Your First Job
                </Link>
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {jobs.map((job) => (
              <Card key={job.id} className="flex flex-col">
                <CardHeader>
                  <CardTitle className="font-headline text-xl truncate" title={job.title}>{job.title}</CardTitle>
                  <CardDescription>
                    Created on: <FormattedDate timestamp={job.createdAt} />
                  </CardDescription>
                </CardHeader>
                <CardContent className="flex-grow">
                  <p className="text-sm text-muted-foreground line-clamp-3">
                    {job.descriptionInput}
                  </p>
                  {job.survey && job.survey.questions && (
                    <div className="mt-2 text-xs">
                      <span className="font-semibold">{job.survey.questions.length}</span> survey questions
                    </div>
                  )}
                </CardContent>
                <CardFooter className="flex justify-between items-center">
                  <div className="text-sm font-medium flex items-center">
                      <Users className="mr-2 h-4 w-4 text-muted-foreground" />
                      {job.applicants?.length || 0} Applicant{job.applicants?.length === 1 ? '' : 's'}
                    </div>
                  <div className="flex items-center gap-2">
                    <Button asChild variant="outline" size="sm">
                      <Link href={`/job/${job.id}/applicants`}>View Dashboard</Link>
                    </Button>
                    <Button
                      variant="destructive"
                      size="icon"
                      onClick={() => openDeleteDialog(job)}
                      title="Delete job"
                      disabled={isLoadingJobs}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardFooter>
              </Card>
            ))}
          </div>
        )}
      </div>

      {jobToDelete && (
        <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
              <AlertDialogDescription>
                This action cannot be undone. This will permanently delete the job
                "<strong className="font-semibold">{jobToDelete.title}</strong>"
                and all of its associated data from Firestore.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel onClick={() => { setIsDeleteDialogOpen(false); setJobToDelete(null); }}>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={handleConfirmDelete} disabled={isLoadingJobs}>
                Delete
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}
    </ClientOnly>
  );
}
