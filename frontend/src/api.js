// Use environment variable for backend URL, fallback to relative path for dev
const API_BASE = import.meta.env.VITE_API_BASE || 
  (typeof window !== 'undefined' && window.location.hostname === 'localhost' 
    ? '' 
    : 'https://meia-8d2bpxwi5-meia.vercel.app');

export async function startAnalysis({ ticker, audio, slides }) {
  const form = new FormData();
  form.append("ticker", ticker);
  form.append("audio", audio);
  form.append("slides", slides);

  const response = await fetch(`${API_BASE}/api/analyze`, {
    method: "POST",
    body: form,
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || "Failed to start analysis");
  }

  return response.json();
}

/**
 * Fetch a single job status with up to `maxRetries` retries on network errors.
 * Transient failures (e.g. brief server hiccup) will be retried with an
 * exponential back-off before surfacing as an error.
 */
export async function fetchJob(jobId, { maxRetries = 3 } = {}) {
  let lastError;
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(`${API_BASE}/api/jobs/${jobId}`);
      if (!response.ok) {
        throw new Error(`Job not found (HTTP ${response.status})`);
      }
      return response.json();
    } catch (err) {
      lastError = err;
      if (attempt < maxRetries) {
        // Exponential back-off: 200ms, 400ms, 800ms
        await new Promise((resolve) => setTimeout(resolve, 200 * 2 ** attempt));
      }
    }
  }
  throw lastError;
}

/**
 * Poll a job until it reaches a terminal state (completed | failed).
 *
 * @param {string} jobId
 * @param {object} options
 * @param {number} [options.intervalMs=2000]   Polling interval in milliseconds.
 * @param {number} [options.timeoutMs=600000]  Max total wait (default 10 min).
 * @param {function} [options.onUpdate]        Called on every poll with the latest job.
 */
export async function pollJob(
  jobId,
  { intervalMs = 2000, timeoutMs = 10 * 60 * 1000, onUpdate } = {}
) {
  const deadline = Date.now() + timeoutMs;

  while (true) {
    if (Date.now() > deadline) {
      throw new Error(`Job ${jobId} timed out after ${timeoutMs / 1000}s`);
    }

    const job = await fetchJob(jobId);
    onUpdate?.(job);

    if (job.status === "completed" || job.status === "failed") {
      return job;
    }

    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
}
