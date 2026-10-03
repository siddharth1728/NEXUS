const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export class ApiError extends Error {
  constructor(public status: number, public data: Record<string, unknown> | null | undefined) {
    const msg = (data?.message as string) || (data?.detail as string) || 'An API error occurred';
    super(msg);
    this.name = 'ApiError';
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-Tenant-ID': '00000000-0000-4000-8000-000000000001',
    ...((options.headers as Record<string, string>) || {}),
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorData;
    try {
      errorData = await response.json();
    } catch {
      errorData = { message: response.statusText };
    }
    throw new ApiError(response.status, errorData);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export const api = {
  get: <T>(endpoint: string, options?: RequestInit) => request<T>(endpoint, { ...options, method: 'GET' }),
  post: <T>(endpoint: string, body?: unknown, options?: RequestInit) => request<T>(endpoint, { ...options, method: 'POST', body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(endpoint: string, body?: unknown, options?: RequestInit) => request<T>(endpoint, { ...options, method: 'PATCH', body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(endpoint: string, options?: RequestInit) => request<T>(endpoint, { ...options, method: 'DELETE' }),
};

// Domain Types
export interface ActionItem {
  id: string;
  tenant_id: string;
  title: string;
  description?: string;
  status: string;
  action_type?: string;
  priority?: "low" | "medium" | "high" | "critical";
  due_date?: string;
  source_context?: {
    document_id?: string;
    document_title?: string;
    location?: string;
    excerpt?: string;
    facts?: string[];
  };
  dependencies?: string[];
  dependents?: string[];
  created_at: string;
  updated_at: string;
}

export interface DocumentItem {
  id: string;
  tenant_id: string;
  title: string;
  source_type: string;
  source_uri?: string;
  processing_status: string;
  facts_count?: number;
  requirements_count?: number;
  actions_count?: number;
  dependencies_count?: number;
  created_at: string;
}

export interface DocumentChunk {
  id: string;
  document_id: string;
  chunk_index: number;
  content: string;
  structural_type?: string;
  source_location?: {
    page?: number;
    section?: string;
    char_start?: number;
    char_end?: number;
  };
}

export interface ExecutionItem {
  id: string;
  tenant_id: string;
  status: string;
  capability: string;
  target?: string;
  policy?: string;
  parameters?: Record<string, unknown>;
  expected_effect?: string;
  evidence?: {
    verified: boolean;
    observations: string[];
    external_reference?: string;
    timestamp?: string;
  };
  created_at: string;
}

export interface ConnectorInfo {
  provider: string;
  status: "connected" | "disconnected" | "degraded";
  capabilities: string[];
  lastChecked?: string;
}
