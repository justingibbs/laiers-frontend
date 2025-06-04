
"use client";

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { useAppStore } from '@/lib/store';
import { useEffect, useState } from 'react';
import type { Job } from '@/lib/types';
import { PlusCircle, Users, FileText } from 'lucide-react';
import LoadingSpinner from '@/components/LoadingSpinner';

export default function HomePage() {
  const jobs = useAppStore((state) => state.getAllJobs());
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    // Return null or a minimal skeleton that won't cause hydration mismatch
    // For critical pages like dashboard, a full page loader might be better than null if it's guaranteed to match
    return (
      <div className="flex justify-center items-center min-h-[calc(100vh-200px)]">
        <LoadingSpinner size={48} />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-3xl font-headline font-bold">Job Dashboard</h1>
        <Button asChild variant="default" size="lg">
          <Link href="/create-job">
            <PlusCircle className="mr-2 h-5 w-5" /> Create New Job & Survey
          </Link>
        </Button>
      </div>

      {jobs.length === 0 ? (
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
                  Created on: {new Date(job.createdAt).toLocaleDateString()}
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-grow">
                <p className="text-sm text-muted-foreground line-clamp-3">
                  {job.descriptionInput}
                </p>
                {job.survey && (
                  <div className="mt-2 text-xs">
                    <span className="font-semibold">{job.survey.questions.length}</span> survey questions
                  </div>
                )}
              </CardContent>
              <CardFooter className="flex justify-between items-center">
                 <div className="text-sm font-medium flex items-center">
                    <Users className="mr-2 h-4 w-4 text-muted-foreground" />
                    {job.applicants.length} Applicant{job.applicants.length === 1 ? '' : 's'}
                  </div>
                <Button asChild variant="outline" size="sm">
                  <Link href={`/job/${job.id}/applicants`}>View Dashboard</Link>
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
