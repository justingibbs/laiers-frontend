
// src/lib/firebase/firestoreService.ts
import {
  collection,
  addDoc,
  getDocs,
  doc,
  getDoc,
  updateDoc,
  deleteDoc,
  query,
  orderBy,
  Timestamp,
  serverTimestamp,
  arrayUnion,
  arrayRemove,
} from 'firebase/firestore';
import { db } from './config';
import type { Job, Applicant } from '@/lib/types';

const JOBS_COLLECTION = 'jobs';

// Helper to convert Firestore Timestamps in a job object
const convertJobTimestamps = (jobData: any): Job => {
  const converted = { ...jobData };
  if (jobData.createdAt instanceof Timestamp) {
    converted.createdAt = jobData.createdAt.toMillis();
  }
  if (jobData.applicants) {
    converted.applicants = jobData.applicants.map((app: any) => {
      if (app.submittedAt instanceof Timestamp) {
        return { ...app, submittedAt: app.submittedAt.toMillis() };
      }
      return app;
    });
  }
  return converted as Job;
};


export const addJobDoc = async (jobData: Omit<Job, 'id' | 'createdAt' | 'applicants'>): Promise<string> => {
  try {
    const docRef = await addDoc(collection(db, JOBS_COLLECTION), {
      ...jobData,
      applicants: [], // Initialize with empty applicants array
      createdAt: serverTimestamp(), // Use server timestamp
    });
    return docRef.id;
  } catch (error) {
    console.error('Error adding job document: ', error);
    throw error;
  }
};

export const getJobDocs = async (): Promise<Job[]> => {
  try {
    const q = query(collection(db, JOBS_COLLECTION), orderBy('createdAt', 'desc'));
    const querySnapshot = await getDocs(q);
    return querySnapshot.docs.map(doc => convertJobTimestamps({ id: doc.id, ...doc.data() } as Job));
  } catch (error) {
    console.error('Error getting job documents: ', error);
    throw error;
  }
};

export const getJobDoc = async (jobId: string): Promise<Job | undefined> => {
  try {
    const docRef = doc(db, JOBS_COLLECTION, jobId);
    const docSnap = await getDoc(docRef);
    if (docSnap.exists()) {
      return convertJobTimestamps({ id: docSnap.id, ...docSnap.data() } as Job);
    }
    return undefined;
  } catch (error) {
    console.error('Error getting job document: ', error);
    throw error;
  }
};

export const updateJobDoc = async (jobId: string, updates: Partial<Omit<Job, 'id' | 'applicants'>>) => {
  try {
    const docRef = doc(db, JOBS_COLLECTION, jobId);
    // Firestore does not allow updating 'id' or server-generated 'createdAt' directly if it's a serverTimestamp.
    // Ensure 'createdAt' and 'id' are not in updates if they are managed by Firestore or the object structure.
    const { id, createdAt, applicants, ...validUpdates } = updates as any;
    await updateDoc(docRef, validUpdates);
  } catch (error) {
    console.error('Error updating job document: ', error);
    throw error;
  }
};

export const deleteJobDoc = async (jobId: string): Promise<void> => {
  try {
    const docRef = doc(db, JOBS_COLLECTION, jobId);
    await deleteDoc(docRef);
  } catch (error) {
    console.error('Error deleting job document: ', error);
    throw error;
  }
};

// Applicant specific functions
export const addApplicantToJobDoc = async (jobId: string, applicantData: Omit<Applicant, 'id' | 'submittedAt'>): Promise<string> => {
  try {
    const jobRef = doc(db, JOBS_COLLECTION, jobId);
    const applicantId = `app-${Date.now()}`; // Generate a simple ID
    const newApplicant = {
      ...applicantData,
      id: applicantId,
      submittedAt: serverTimestamp(), // Use server timestamp
    };
    await updateDoc(jobRef, {
      applicants: arrayUnion(newApplicant)
    });
    return applicantId;
  } catch (error) {
    console.error('Error adding applicant to job: ', error);
    throw error;
  }
};

export const updateApplicantInJobDoc = async (jobId: string, applicantId: string, updates: Partial<Omit<Applicant, 'id' | 'jobId' | 'submittedAt'>>) => {
  try {
    const jobRef = doc(db, JOBS_COLLECTION, jobId);
    const jobSnap = await getDoc(jobRef);
    if (!jobSnap.exists()) {
      throw new Error("Job not found for updating applicant");
    }
    const jobData = jobSnap.data() as Job;
    const applicants = jobData.applicants || [];
    const applicantIndex = applicants.findIndex(app => app.id === applicantId);

    if (applicantIndex === -1) {
      throw new Error("Applicant not found in job");
    }

    const updatedApplicants = [...applicants];
    // Ensure `id`, `jobId`, `submittedAt` are not in updates as they shouldn't change this way
    const { id, jobId: applicantJobId, submittedAt, ...validUpdates } = updates as any;

    updatedApplicants[applicantIndex] = {
      ...updatedApplicants[applicantIndex],
      ...validUpdates,
    };

    await updateDoc(jobRef, { applicants: updatedApplicants });
  } catch (error) {
    console.error('Error updating applicant in job: ', error);
    throw error;
  }
};
