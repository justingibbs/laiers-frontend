
"use client";

import { create } from 'zustand';
import type { Job, Applicant, Survey } from './types';
import { 
  addJobDoc, 
  getJobDocs, 
  getJobDoc as getJobDocFromFirestore, 
  updateJobDoc, 
  deleteJobDoc,
  addApplicantToJobDoc,
  updateApplicantInJobDoc
} from './firebase/firestoreService';

interface AppState {
  jobs: Job[];
  currentJob: Job | null;
  isLoading: boolean;
  error: string | null;
  
  fetchJobs: () => Promise<void>;
  fetchJobById: (jobId: string) => Promise<Job | undefined>;
  
  createJob: (jobData: {
    title: string;
    descriptionInput: string;
    generatedListingText: string;
  }) => Promise<string | undefined>;

  updateJob: (jobId: string, updates: Partial<Omit<Job, 'id' | 'applicants' | 'createdAt'>>) => Promise<void>;
  deleteJob: (jobId: string) => Promise<void>;
  
  addApplicant: (jobId: string, applicantData: Omit<Applicant, 'id' | 'submittedAt'>) => Promise<string | undefined>;
  updateApplicant: (jobId: string, applicantId: string, updates: Partial<Omit<Applicant, 'id' | 'jobId' | 'submittedAt'>>) => Promise<void>;
  
  // For UI consistency, we can still have these getters that operate on the local cache
  getJobFromCache: (jobId: string) => Job | undefined;
  getApplicantFromCache: (jobId: string, applicantId: string) => Applicant | undefined;
  getAllJobsFromCache: () => Job[];
}

export const useAppStore = create<AppState>((set, get) => ({
  jobs: [],
  currentJob: null,
  isLoading: false,
  error: null,

  fetchJobs: async () => {
    set({ isLoading: true, error: null });
    try {
      const jobs = await getJobDocs();
      set({ jobs, isLoading: false });
    } catch (error) {
      console.error("Error fetching jobs from Firestore:", error);
      set({ error: (error as Error).message || 'Failed to fetch jobs', isLoading: false });
    }
  },

  fetchJobById: async (jobId: string) => {
    set({ isLoading: true, error: null, currentJob: null });
    try {
      const job = await getJobDocFromFirestore(jobId);
      set({ currentJob: job || null, isLoading: false });
      // Also update the jobs array if the job is fetched individually and not in the list or outdated
      if (job) {
        const existingJobs = get().jobs;
        const jobIndex = existingJobs.findIndex(j => j.id === jobId);
        if (jobIndex > -1) {
          const updatedJobs = [...existingJobs];
          updatedJobs[jobIndex] = job;
          set({ jobs: updatedJobs });
        } else {
          set({ jobs: [...existingJobs, job] });
        }
      }
      return job;
    } catch (error) {
      console.error(`Error fetching job ${jobId} from Firestore:`, error);
      set({ error: (error as Error).message || `Failed to fetch job ${jobId}`, isLoading: false });
      return undefined;
    }
  },

  createJob: async (jobData) => {
    set({ isLoading: true, error: null });
    try {
      // createdAt will be set by Firestore, applicants initialized as empty by addJobDoc
      const newJobId = await addJobDoc(jobData);
      await get().fetchJobs(); // Refresh the list
      set({ isLoading: false });
      return newJobId;
    } catch (error) {
      console.error("Error creating job in Firestore:", error);
      set({ error: (error as Error).message || 'Failed to create job', isLoading: false });
      return undefined;
    }
  },

  updateJob: async (jobId, updates) => {
    set({ isLoading: true, error: null });
    try {
      await updateJobDoc(jobId, updates);
      // Optimistically update local cache or re-fetch
      const currentJobs = get().jobs;
      const jobIndex = currentJobs.findIndex(j => j.id === jobId);
      if (jobIndex > -1) {
        const updatedJobs = [...currentJobs];
        updatedJobs[jobIndex] = { ...updatedJobs[jobIndex], ...updates, applicants: updatedJobs[jobIndex].applicants }; // preserve applicants
         // If survey is part of updates, ensure it's correctly merged
        if (updates.survey) {
          updatedJobs[jobIndex].survey = { ...updatedJobs[jobIndex].survey, ...updates.survey } as Survey;
        }
        set({ jobs: updatedJobs });
      }
      if (get().currentJob?.id === jobId) {
        set({ currentJob: { ...get().currentJob!, ...updates, applicants: get().currentJob!.applicants } as Job });
         if (updates.survey && get().currentJob) {
            set(state => ({ currentJob: { ...state.currentJob!, survey: { ...state.currentJob!.survey, ...updates.survey } as Survey }}));
        }
      }
      set({ isLoading: false });
    } catch (error) {
      console.error(`Error updating job ${jobId} in Firestore:`, error);
      set({ error: (error as Error).message || `Failed to update job ${jobId}`, isLoading: false });
    }
  },

  deleteJob: async (jobId: string) => {
    set({ isLoading: true, error: null });
    try {
      await deleteJobDoc(jobId);
      set(state => ({
        jobs: state.jobs.filter(job => job.id !== jobId),
        isLoading: false,
      }));
    } catch (error) {
      console.error(`Error deleting job ${jobId} from Firestore:`, error);
      set({ error: (error as Error).message || `Failed to delete job ${jobId}`, isLoading: false });
    }
  },
  
  addApplicant: async (jobId, applicantData) => {
    set({ isLoading: true, error: null });
    try {
      const newApplicantId = await addApplicantToJobDoc(jobId, applicantData);
      await get().fetchJobById(jobId); // Refresh the specific job to get the new applicant
      set({ isLoading: false });
      return newApplicantId;
    } catch (error) {
      console.error(`Error adding applicant to job ${jobId}:`, error);
      set({ error: (error as Error).message || 'Failed to add applicant', isLoading: false });
      return undefined;
    }
  },

  updateApplicant: async (jobId, applicantId, updates) => {
     set({ isLoading: true, error: null });
    try {
      await updateApplicantInJobDoc(jobId, applicantId, updates);
      await get().fetchJobById(jobId); // Refresh the specific job
      set({ isLoading: false });
    } catch (error) {
      console.error(`Error updating applicant ${applicantId} in job ${jobId}:`, error);
      set({ error: (error as Error).message || 'Failed to update applicant', isLoading: false });
    }
  },

  // Getters for local cache
  getJobFromCache: (jobId) => get().jobs.find(j => j.id === jobId) || (get().currentJob?.id === jobId ? get().currentJob : undefined),
  getApplicantFromCache: (jobId, applicantId) => {
    const job = get().getJobFromCache(jobId);
    return job?.applicants.find(app => app.id === applicantId);
  },
  getAllJobsFromCache: () => get().jobs.sort((a, b) => (b.createdAt || 0) - (a.createdAt || 0)),

}));
