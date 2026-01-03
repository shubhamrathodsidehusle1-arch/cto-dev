import { Job } from '@/types';
import { Calendar, Clock, Film, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface JobCardProps {
  job: Job;
}

export default function JobCard({ job }: JobCardProps) {
  const statusColors = {
    queued: 'bg-gray-100 text-gray-800',
    processing: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  };

  const StatusIcon = {
    queued: Clock,
    processing: Loader2,
    completed: CheckCircle,
    failed: AlertCircle,
  }[job.status];

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden border border-gray-200">
      <div className="p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Film className="h-5 w-5 text-gray-400" />
            <span className="text-sm font-medium text-gray-900 truncate max-w-[200px]">
              {job.prompt}
            </span>
          </div>
          <span
            className={cn(
              'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
              statusColors[job.status]
            )}
          >
            <StatusIcon className={cn('mr-1 h-3 w-3', job.status === 'processing' && 'animate-spin')} />
            {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
          </span>
        </div>

        <div className="space-y-2">
          <div className="flex items-center text-sm text-gray-500">
            <Calendar className="mr-1.5 h-4 w-4 flex-shrink-0" />
            {new Date(job.createdAt).toLocaleString()}
          </div>
          {job.generationTimeMs && (
            <div className="flex items-center text-sm text-gray-500">
              <Clock className="mr-1.5 h-4 w-4 flex-shrink-0" />
              {(job.generationTimeMs / 1000).toFixed(2)}s
            </div>
          )}
        </div>

        {job.errorMessage && (
          <div className="mt-4 text-sm text-red-600 bg-red-50 p-2 rounded">
            {job.errorMessage}
          </div>
        )}

        {job.status === 'completed' && job.result?.videoUrl && (
          <div className="mt-4">
            <video
              src={job.result.videoUrl}
              controls
              className="w-full rounded-md border border-gray-200"
              poster={job.result.thumbnailUrl}
            />
          </div>
        )}
      </div>
      <div className="bg-gray-50 px-5 py-3 flex justify-between items-center">
        <div className="text-xs text-gray-500">
          ID: {job.id.slice(0, 8)}...
        </div>
        <div className="text-xs text-gray-500">
          Provider: {job.usedProvider || 'Pending'}
        </div>
      </div>
    </div>
  );
}
