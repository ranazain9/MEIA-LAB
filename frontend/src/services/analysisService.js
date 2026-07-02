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

let latestBackendSnapshot = null;

export async function getDashboardAnalysis() {
  await delay(360);
  if (latestBackendSnapshot?.dashboard) {
    return {
      analysis: latestBackendSnapshot.dashboard,
      agents: agentStatuses,
      quality: qualityMetrics,
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
  return latestBackendSnapshot?.evidence || evidenceItems;
}

export async function getBrief() {
  await delay(340);
  return latestBackendSnapshot?.brief || brief;
}

export async function getProcessingSteps() {
  await delay(300);
  return processingSteps;
}

export function applyBackendJob(job) {
  latestBackendSnapshot = normalizeJobToAnalysis(job);
  return latestBackendSnapshot;
}

export { fetchJob, normalizeJobToAnalysis, pollJob, startAnalysis };
