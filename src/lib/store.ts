"use client";

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { Job, Applicant } from './types';

interface AppState {
  jobs: Record<string, Job>;
  addJob: (job: Job) => void;
  updateJob: (jobId: string, updates: Partial<Omit<Job, 'id' | 'applicants' | 'createdAt'>>) => void;
  addApplicant: (jobId: string, applicant: Applicant) => void;
  updateApplicant: (jobId: string, applicantId: string, updates: Partial<Omit<Applicant, 'id' | 'jobId' | 'submittedAt'>>) => void;
  getJob: (jobId: string) => Job | undefined;
  getApplicant: (jobId: string, applicantId: string) => Applicant | undefined;
  getAllJobs: () => Job[];
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      jobs: {},
      addJob: (job) =>
        set((state) => ({
          jobs: { ...state.jobs, [job.id]: job },
        })),
      updateJob: (jobId, updates) =>
        set((state) => {
          const job = state.jobs[jobId];
          if (job) {
            return {
              jobs: { ...state.jobs, [jobId]: { ...job, ...updates } },
            };
          }
          return state;
        }),
      addApplicant: (jobId, applicant) =>
        set((state) => {
          const job = state.jobs[jobId];
          if (job) {
            const updatedApplicants = [...job.applicants, applicant];
            return {
              jobs: { ...state.jobs, [jobId]: { ...job, applicants: updatedApplicants } },
            };
          }
          return state;
        }),
      updateApplicant: (jobId, applicantId, updates) =>
        set((state) => {
          const job = state.jobs[jobId];
          if (job) {
            const applicantIndex = job.applicants.findIndex(app => app.id === applicantId);
            if (applicantIndex > -1) {
              const updatedApplicants = [...job.applicants];
              updatedApplicants[applicantIndex] = { ...updatedApplicants[applicantIndex], ...updates };
              return {
                jobs: { ...state.jobs, [jobId]: { ...job, applicants: updatedApplicants } },
              };
            }
          }
          return state;
        }),
      getJob: (jobId) => get().jobs[jobId],
      getApplicant: (jobId, applicantId) => {
        const job = get().jobs[jobId];
        return job?.applicants.find(app => app.id === applicantId);
      },
      getAllJobs: () => Object.values(get().jobs).sort((a, b) => b.createdAt - a.createdAt),
    }),
    {
      name: 'laiers-ai-storage', 
      storage: createJSONStorage(() => localStorage), 
    }
  )
);
