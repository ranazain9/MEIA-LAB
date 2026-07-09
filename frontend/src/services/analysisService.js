import { fetchJob, pollJob, startAnalysis } from "../api.js";
import {
  agentStatuses,
  brief,
  dashboardAnalysis,
  evidenceItems,
  processingSteps,
  qualityMetrics,
  riskItems,
} from "../data/mockAnalysis.js";
import { normalizeJobToAnalysis } from "./backendAdapter.js";

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const LIVE_JOB_STORAGE_KEY = "meia.latestBackendJob";

let latestBackendSnapshot = null;

function readStoredJob() {
  try {
    const value = window.localStorage.getItem(LIVE_JOB_STORAGE_KEY);
    return value ? JSON.parse(value) : null;
  } catch {
    return null;
  }
}

function writeStoredJob(job) {
  try {
    window.localStorage.setItem(LIVE_JOB_STORAGE_KEY, JSON.stringify(job));
  } catch {
    // localStorage can be unavailable in restricted browser contexts.
  }
}

function clearStoredJob() {
  try {
    window.localStorage.removeItem(LIVE_JOB_STORAGE_KEY);
  } catch {
    // Ignore storage failures; in-memory state still works for this tab.
  }
}

async function ensureBackendSnapshot() {
  if (latestBackendSnapshot) return latestBackendSnapshot;

  const storedJob = readStoredJob();
  if (!storedJob) return null;

  if (storedJob.status === "completed" && storedJob.result) {
    latestBackendSnapshot = normalizeJobToAnalysis(storedJob);
    return latestBackendSnapshot;
  }

  if (!storedJob.job_id) return null;

  try {
    const freshJob = await fetchJob(storedJob.job_id, { maxRetries: 1 });
    if (freshJob.status === "completed" && freshJob.result) {
      writeStoredJob(freshJob);
      latestBackendSnapshot = normalizeJobToAnalysis(freshJob);
      return latestBackendSnapshot;
    }
  } catch {
    clearStoredJob();
  }

  return null;
}

export async function getDashboardAnalysis() {
  await delay(360);
  await ensureBackendSnapshot();
  if (latestBackendSnapshot?.dashboard) {
    return {
      analysis: latestBackendSnapshot.dashboard,
      agents: latestBackendSnapshot.agents || agentStatuses,
      quality: latestBackendSnapshot.quality || qualityMetrics,
      risks: latestBackendSnapshot.risks,
    };
  }
  return {
    analysis: dashboardAnalysis,
    agents: agentStatuses,
    quality: qualityMetrics,
    risks: riskItems,
  };
}

export async function getEvidenceItems() {
  await delay(320);
  await ensureBackendSnapshot();
  return latestBackendSnapshot?.evidence || evidenceItems;
}

export async function getClaimItems() {
  await delay(320);
  await ensureBackendSnapshot();
  if (latestBackendSnapshot?.claims) {
    return latestBackendSnapshot.claims;
  }
  return evidenceItems;
}

export async function getBrief() {
  await delay(340);
  await ensureBackendSnapshot();
  if (latestBackendSnapshot?.brief) {
    return {
      ...latestBackendSnapshot.brief,
      company: latestBackendSnapshot.dashboard?.company || dashboardAnalysis.company,
      period: latestBackendSnapshot.dashboard?.period || dashboardAnalysis.period,
      generated: latestBackendSnapshot.brief.generated || latestBackendSnapshot.dashboard?.generated || brief.generated,
    };
  }
  return {
    ...brief,
    company: dashboardAnalysis.company,
    period: dashboardAnalysis.period,
  };
}

export async function getProcessingSteps() {
  await delay(300);
  return processingSteps;
}

export function applyBackendJob(job) {
  writeStoredJob(job);
  latestBackendSnapshot = normalizeJobToAnalysis(job);
  return latestBackendSnapshot;
}

/** Returns true when a real backend job has been applied and its data is available. */
export function isLiveData() {
  return latestBackendSnapshot !== null;
}

/** Clear the snapshot — call before starting a new job so stale data is not shown. */
export function clearBackendSnapshot() {
  latestBackendSnapshot = null;
  clearStoredJob();
}

export { fetchJob, normalizeJobToAnalysis, pollJob, startAnalysis };

