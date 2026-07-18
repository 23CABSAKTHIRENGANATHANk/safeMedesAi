const getApiBaseUrl = () => {
  let url = import.meta.env.VITE_API_URL || "/api";
  
  // Clean up trailing slash
  if (url.endsWith("/")) {
    url = url.slice(0, -1);
  }
  
  // Auto-correct spelling and append missing '/api' for Render deployments
  if (url.includes("safemedsai.onrender.com")) {
    url = "https://safemedesai.onrender.com/api";
  } else if (url.includes("safemedesai.onrender.com") && !url.endsWith("/api")) {
    url = "https://safemedesai.onrender.com/api";
  }
  
  return url;
};

const API_BASE_URL = getApiBaseUrl();

export interface VerifyPayload {
  name: string;
  manufacturer?: string;
  batch?: string;
}

export interface Result {
  status: "safe" | "unsafe" | "warning" | "unknown";
  name: string;
  batch?: string;
  authority?: string;
  reason?: string;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  if (!response.ok) {
    const text = await response.text().catch(() => response.statusText);
    throw new Error(`API request failed (${response.status}): ${text}`);
  }
  return response.json();
}

export async function verifyMedicine(payload: VerifyPayload): Promise<Result> {
  return request<Result>(`/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

// Domain types
export interface Medicine {
  id?: string;
  name: string;
  manufacturer?: string;
  ndc?: string;
  notes?: string;
}

export interface AlertRecord {
  id?: string;
  authority?: string;
  title?: string;
  description?: string;
  date?: string;
}

export interface RecallRecord {
  id?: string;
  authority?: string;
  title?: string;
  description?: string;
  date?: string;
}

// Reusable API services
export async function getMedicines(
  page = 1,
  limit = 20,
): Promise<{ data: Medicine[]; page: number; limit: number; total?: number }> {
  return request(`/medicines?page=${page}&limit=${limit}`);
}

export async function getMedicine(name: string): Promise<Medicine> {
  return request(`/medicine/${encodeURIComponent(name)}`);
}

export async function getAlerts(
  page = 1,
  limit = 20,
): Promise<{ data: AlertRecord[]; page: number; limit: number; total?: number }> {
  return request(`/alerts?page=${page}&limit=${limit}`);
}

export async function getRecalls(
  page = 1,
  limit = 20,
): Promise<{ data: RecallRecord[]; page: number; limit: number; total?: number }> {
  return request(`/recalls?page=${page}&limit=${limit}`);
}
export async function searchMedicines(
  q: string,
  page = 1,
  limit = 20,
): Promise<{ data: Medicine[]; page: number; limit: number; total?: number }> {
  return request(`/search?medicine=${encodeURIComponent(q)}&page=${page}&limit=${limit}`);
}
