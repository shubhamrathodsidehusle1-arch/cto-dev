export type JobStatus = 'queued' | 'processing' | 'completed' | 'failed' | 'cancelled';

export interface Job {
  id: string;
  userId: string;
  status: JobStatus;
  prompt: string;
  metadata?: Record<string, any>;
  result?: {
    videoUrl?: string;
    thumbnailUrl?: string;
    [key: string]: any;
  };
  retryCount: number;
  maxRetries: number;
  usedProvider?: string;
  usedModel?: string;
  generationTimeMs?: number;
  errorMessage?: string;
  createdAt: string;
  updatedAt: string;
  startedAt?: string;
  completedAt?: string;
}

export interface CreateJobRequest {
  userId: string;
  prompt: string;
  metadata?: Record<string, any>;
  maxRetries?: number;
}

export interface ProviderHealth {
  provider: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  lastCheckedAt: string;
  consecutiveFailures: number;
  avgResponseTimeMs: number;
  costPerRequest: number;
}
