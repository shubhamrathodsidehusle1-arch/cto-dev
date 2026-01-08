/**
 * API Service for backend communication
 */

export interface ApiClientConfig {
  baseURL: string;
  getAccessToken: () => string | null;
  onUnauthorized?: () => void;
}

class ApiClient {
  private baseURL: string;
  private getAccessToken: () => string | null;
  private onUnauthorized?: () => void;

  constructor(config: ApiClientConfig) {
    this.baseURL = config.baseURL;
    this.getAccessToken = config.getAccessToken;
    this.onUnauthorized = config.onUnauthorized;
  }

  private getHeaders(): Record<string, string> {
    const token = this.getAccessToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return headers;
  }

  private async handleResponse(response: Response): Promise<any> {
    if (!response.ok) {
      if (response.status === 401 && this.onUnauthorized) {
        this.onUnauthorized();
      }

      const error = await response.json().catch(() => ({
        error: 'An unexpected error occurred',
      }));

      throw new Error(error.error || error.message || 'Request failed');
    }

    return response.json();
  }

  async get<T>(path: string): Promise<T> {
    const response = await fetch(`${this.baseURL}${path}`, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse(response);
  }

  async post<T>(path: string, data?: any): Promise<T> {
    const response = await fetch(`${this.baseURL}${path}`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: data ? JSON.stringify(data) : undefined,
    });

    return this.handleResponse(response);
  }

  async patch<T>(path: string, data?: any): Promise<T> {
    const response = await fetch(`${this.baseURL}${path}`, {
      method: 'PATCH',
      headers: this.getHeaders(),
      body: data ? JSON.stringify(data) : undefined,
    });

    return this.handleResponse(response);
  }

  async delete<T>(path: string): Promise<T> {
    const response = await fetch(`${this.baseURL}${path}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });

    return this.handleResponse(response);
  }
}

// Initialize API client with environment configuration
const apiClient = new ApiClient({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  getAccessToken: () => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('accessToken');
    }
    return null;
  },
  onUnauthorized: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('user');
      window.location.href = '/';
    }
  },
});

// Types
export interface User {
  id: string;
  email: string;
  createdAt: string;
  updatedAt: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Job {
  id: string;
  userId: string;
  projectId: string | null;
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'cancelled';
  prompt: string;
  metadata: any;
  result: any;
  startedAt: string | null;
  completedAt: string | null;
  retryCount: number;
  maxRetries: number;
  celeryTaskId: string | null;
  usedProvider: string | null;
  usedModel: string | null;
  generationTimeMs: number | null;
  errorMessage: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface Project {
  id: string;
  userId: string;
  name: string;
  description: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface JobListResponse {
  jobs: Job[];
  total: number;
  skip: number;
  take: number;
}

export interface ProjectListResponse {
  projects: Project[];
  total: number;
  skip: number;
  take: number;
}

export interface JobStatsResponse {
  total: number;
  by_status: Record<string, number>;
  success_rate: number;
  avg_generation_time_ms: number | null;
}

// Auth API
export const authApi = {
  register: async (email: string, password: string): Promise<User> => {
    return apiClient.post<User>('/auth/register', { email, password });
  },

  login: async (email: string, password: string): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>('/auth/login', {
      email,
      password,
    });

    // Store tokens
    if (typeof window !== 'undefined') {
      localStorage.setItem('accessToken', response.access_token);
      localStorage.setItem('refreshToken', response.refresh_token);
    }

    return response;
  },

  refreshToken: async (refreshToken: string): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    });

    // Update tokens
    if (typeof window !== 'undefined') {
      localStorage.setItem('accessToken', response.access_token);
      localStorage.setItem('refreshToken', response.refresh_token);
    }

    return response;
  },

  getCurrentUser: async (): Promise<User> => {
    return apiClient.get<User>('/auth/me');
  },

  logout: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('user');
    }
  },
};

// Jobs API
export const jobsApi = {
  create: async (data: {
    prompt: string;
    projectId?: string;
    model?: string;
    resolution?: string;
    quality?: string;
    duration?: number;
    metadata?: any;
    maxRetries?: number;
  }): Promise<Job> => {
    return apiClient.post<Job>('/jobs', data);
  },

  list: async (params?: {
    status?: string;
    projectId?: string;
    skip?: number;
    take?: number;
  }): Promise<JobListResponse> => {
    const queryParams = new URLSearchParams();
    if (params?.status) queryParams.append('status', params.status);
    if (params?.projectId) queryParams.append('projectId', params.projectId);
    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString());
    if (params?.take !== undefined) queryParams.append('take', params.take.toString());

    const queryString = queryParams.toString();
    return apiClient.get<JobListResponse>(`/jobs${queryString ? `?${queryString}` : ''}`);
  },

  get: async (jobId: string): Promise<Job> => {
    return apiClient.get<Job>(`/jobs/${jobId}`);
  },

  cancel: async (jobId: string): Promise<Job> => {
    return apiClient.post<Job>(`/jobs/${jobId}/cancel`);
  },

  retry: async (jobId: string): Promise<Job> => {
    return apiClient.post<Job>(`/jobs/${jobId}/retry`);
  },

  delete: async (jobId: string): Promise<void> => {
    return apiClient.delete<void>(`/jobs/${jobId}`);
  },

  getStats: async (): Promise<JobStatsResponse> => {
    return apiClient.get<JobStatsResponse>('/jobs/stats/summary');
  },
};

// Projects API
export const projectsApi = {
  create: async (data: { name: string; description?: string }): Promise<Project> => {
    return apiClient.post<Project>('/projects', data);
  },

  list: async (params?: { skip?: number; take?: number }): Promise<ProjectListResponse> => {
    const queryParams = new URLSearchParams();
    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString());
    if (params?.take !== undefined) queryParams.append('take', params.take.toString());

    const queryString = queryParams.toString();
    return apiClient.get<ProjectListResponse>(`/projects${queryString ? `?${queryString}` : ''}`);
  },

  get: async (projectId: string): Promise<Project> => {
    return apiClient.get<Project>(`/projects/${projectId}`);
  },

  update: async (
    projectId: string,
    data: { name?: string; description?: string }
  ): Promise<Project> => {
    return apiClient.patch<Project>(`/projects/${projectId}`, data);
  },

  delete: async (projectId: string): Promise<void> => {
    return apiClient.delete<void>(`/projects/${projectId}`);
  },
};

export default apiClient;
