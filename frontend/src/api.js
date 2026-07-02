const API_BASE = import.meta.env.VITE_API_BASE || "";

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

export async function fetchJob(jobId) {
  const response = await fetch(`${API_BASE}/api/jobs/${jobId}`);
  if (!response.ok) {
    throw new Error("Job not found");
  }
  return response.json();
}

export async function pollJob(jobId, { intervalMs = 2000, onUpdate } = {}) {
  while (true) {
    const job = await fetchJob(jobId);
    onUpdate?.(job);

    if (job.status === "completed" || job.status === "failed") {
      return job;
    }

    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
}
