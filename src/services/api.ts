const getApiBaseUrl = () => {
  const rawEnvUrl = import.meta.env.VITE_API_URL?.trim();
  if (rawEnvUrl) {
    return rawEnvUrl.replace(/\/+$/, "");
  }

  if (typeof window === "undefined") {
    return "/api";
  }

  const hostname = window.location.hostname;
  if (hostname === "localhost" || hostname === "127.0.0.1") {
    return "/api";
  }

  if (hostname.endsWith("vercel.app") || hostname.endsWith("vercel.sh")) {
    return "/api";
  }

  return "/api";
};

const API_BASE_URL = getApiBaseUrl();

// Fallback backend hosts to try when the primary `/api` path returns a 404 Not Found
const FALLBACK_API_BASES = [
  // Common Render service slugs we might have used
  "https://safemeds-ai-backend.onrender.com/api",
  "https://safe-meds-ai-backend.onrender.com/api",
  "https://safe-medes-ai-backend.onrender.com/api",
  "https://safemeds-ai.onrender.com/api",
  "https://safe-medes-ai.onrender.com/api",
];

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
  const url = `${API_BASE_URL}${path}`;

  const doFetch = async (u: string) => {
    const res = await fetch(u, options);
    return res;
  };

  let response = await doFetch(url);

  // If we get a FastAPI 404 Not Found with JSON detail, try fallbacks
  if (response.status === 404) {
    try {
      const body = await response.clone().json().catch(() => null);
      if (body && typeof body.detail === "string") {
        // Try fallback hostnames (useful when rewrite points to the wrong Render slug)
        for (const base of FALLBACK_API_BASES) {
          try {
            const tryUrl = `${base.replace(/\/+$/, "")}${path}`;
            const alt = await doFetch(tryUrl);
            if (alt.ok) return alt.json();
            // if alt returned 404, continue to next
          } catch (e) {
            // ignore and try next
          }
        }
      }
    } catch (e) {
      // ignore parsing errors and fall through
    }
  }

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
