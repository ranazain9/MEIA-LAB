import { mapJobToProcessingState } from "./resultParser.js";

const ANALYSIS_STEP_DURATIONS_MS = [2500, 4000, 3500, 3000, 3500, 2500];

/**
 * Drive ProcessingPage cards from backend job status.
 */
export function createPipelineController(steps, callbacks) {
  const { onStatusesChange, onActiveIndexChange } = callbacks;
  let analysisTimers = [];
  let analysisAnimationStarted = false;

  function clearAnalysisTimers() {
    analysisTimers.forEach((timer) => window.clearTimeout(timer));
    analysisTimers = [];
    analysisAnimationStarted = false;
  }

  function applyJob(job) {
    const backendStatus = job?.status || "pending";
    const backendStep = job?.current_step || "queued";

    if (backendStatus === "completed") {
      completeAll();
      return;
    }

    if (backendStatus === "failed") {
      failRemaining();
      return;
    }

    if (analysisAnimationStarted && backendStep === "analysis") {
      return;
    }

    const { statuses, activeIndex } = mapJobToProcessingState(job, steps);
    onStatusesChange(statuses);
    onActiveIndexChange(activeIndex);

    if (backendStatus === "running" && backendStep === "analysis") {
      startAnalysisAnimation(Math.max(activeIndex, 2));
    }
  }

  function startAnalysisAnimation(fromIndex = 2) {
    analysisAnimationStarted = true;

    let accumulated = 0;
    for (let index = Math.max(fromIndex, 2); index < steps.length; index += 1) {
      const duration = ANALYSIS_STEP_DURATIONS_MS[index - 2] ?? 2500;
      accumulated += duration;

      const timer = window.setTimeout(() => {
        onActiveIndexChange(index);
        onStatusesChange((current) => {
          const next = { ...current };
          steps.forEach((step, stepIndex) => {
            if (stepIndex < index) next[step.id] = "Complete";
            else if (stepIndex === index) next[step.id] = "Running";
            else if (next[step.id] !== "Complete") next[step.id] = "Pending";
          });
          return next;
        });
      }, accumulated);

      analysisTimers.push(timer);
    }
  }

  function reset(initialStatus = "Pending") {
    clearAnalysisTimers();
    onStatusesChange(Object.fromEntries(steps.map((step) => [step.id, initialStatus])));
    onActiveIndexChange(-1);
  }

  function completeAll() {
    clearAnalysisTimers();
    onStatusesChange(Object.fromEntries(steps.map((step) => [step.id, "Complete"])));
    onActiveIndexChange(-1);
  }

  function failRemaining() {
    clearAnalysisTimers();
    onStatusesChange((current) => {
      const next = { ...current };
      steps.forEach((step) => {
        if (next[step.id] !== "Complete") next[step.id] = "Error";
      });
      return next;
    });
    onActiveIndexChange(-1);
  }

  function dispose() {
    clearAnalysisTimers();
  }

  return {
    applyJob,
    reset,
    completeAll,
    failRemaining,
    dispose,
  };
}
