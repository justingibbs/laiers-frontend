
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
      const errorMessage = (error instanceof Error ? error.message : String(error)) || 'Failed to fetch jobs';
      console.error("Error fetching jobs from Firestore:", errorMessage, error);
      set({ error: errorMessage, isLoading: false });
    }
  },

  fetchJobById: async (jobId: string) => {
    set({ isLoading: true, error: null, currentJob: null });
    try {
      const job = await getJobDocFromFirestore(jobId);
      set({ currentJob: job || null, isLoading: false });
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
      const errorMessage = (error instanceof Error ? error.message : String(error)) || `Failed to fetch job ${jobId}`;
      console.error(`Error fetching job ${jobId} from Firestore:`, errorMessage, error);
      set({ error: errorMessage, isLoading: false });
      return undefined;
    }
  },

  createJob: async (jobData) => {
    set({ isLoading: true, error: null });
    try {
      const newJobId = await addJobDoc(jobData);
      if (!newJobId) {
        throw new Error("Failed to create job in Firestore, addJobDoc returned no ID.");
      }
      await get().fetchJobs(); 
      set({ isLoading: false });
      return newJobId;
    } catch (error) {
      const errorMessage = (error instanceof Error ? error.message : String(error)) || 'Failed to create job';
      console.error("Error creating job in Firestore (store):", errorMessage, error);
      set({ error: errorMessage, isLoading: false });
      return undefined; 
    }
  },

  updateJob: async (jobId, updates) => {
    set({ isLoading: true, error: null });
    try {
      await updateJobDoc(jobId, updates);
      const currentJobs = get().jobs;
      const jobIndex = currentJobs.findIndex(j => j.id === jobId);
      if (jobIndex > -1) {
        const updatedJobs = [...currentJobs];
        const currentApplicants = updatedJobs[jobIndex].applicants;
        updatedJobs[jobIndex] = { ...updatedJobs[jobIndex], ...updates, applicants: currentApplicants };
        if (updates.survey) {
          updatedJobs[jobIndex].survey = { ...updatedJobs[jobIndex].survey, ...updates.survey } as Survey;
        }
        set({ jobs: updatedJobs });
      }
      if (get().currentJob?.id === jobId) {
        const currentJobApplicants = get().currentJob!.applicants;
        set(state => ({ 
          currentJob: { 
            ...state.currentJob!, 
            ...updates, 
            applicants: currentJobApplicants,
            survey: updates.survey ? { ...state.currentJob!.survey, ...updates.survey } as Survey : state.currentJob!.survey 
          } 
        }));
      }
      set({ isLoading: false });
    } catch (error) {
      const errorMessage = (error instanceof Error ? error.message : String(error)) || `Failed to update job ${jobId}`;
      console.error(`Error updating job ${jobId} in Firestore:`, errorMessage, error);
      set({ error: errorMessage, isLoading: false });
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
      const errorMessage = (error instanceof Error ? error.message : String(error)) || `Failed to delete job ${jobId}`;
      console.error(`Error deleting job ${jobId} from Firestore:`, errorMessage, error);
      set({ error: errorMessage, isLoading: false });
    }
  },
  
  addApplicant: async (jobId, applicantData) => {
    set({ isLoading: true, error: null });
    try {
      const newApplicantId = await addApplicantToJobDoc(jobId, applicantData);
      if (!newApplicantId) {
        throw new Error("Failed to add applicant, addApplicantToJobDoc returned no ID.");
      }
      await get().fetchJobById(jobId); 
      set({ isLoading: false });
      return newApplicantId;
    } catch (error) {
      const errorMessage = (error instanceof Error ? error.message : String(error)) || 'Failed to add applicant';
      console.error(`Error adding applicant to job ${jobId}:`, errorMessage, error);
      set({ error: errorMessage, isLoading: false });
      return undefined;
    }
  },

  updateApplicant: async (jobId, applicantId, updates) => {
     set({ isLoading: true, error: null });
    try {
      await updateApplicantInJobDoc(jobId, applicantId, updates);
      await get().fetchJobById(jobId); 
      set({ isLoading: false });
    } catch (error) {
      const errorMessage = (error instanceof Error ? error.message : String(error)) || 'Failed to update applicant';
      console.error(`Error updating applicant ${applicantId} in job ${jobId}:`, errorMessage, error);
      set({ error: errorMessage, isLoading: false });
    }
  },

  getJobFromCache: (jobId) => get().jobs.find(j => j.id === jobId) || (get().currentJob?.id === jobId ? get().currentJob : undefined),
  getApplicantFromCache: (jobId, applicantId) => {
    const job = get().getJobFromCache(jobId);
    return job?.applicants.find(app => app.id === applicantId);
  },
  getAllJobsFromCache: () => get().jobs.sort((a, b) => (b.createdAt || 0) - (a.createdAt || 0)),

}));

