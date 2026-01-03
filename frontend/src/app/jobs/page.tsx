'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Job } from '@/types';
import JobCard from '@/components/JobCard';
import { RefreshCcw, Plus } from 'lucide-react';
import Link from 'next/link';

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchJobs = async () => {
    try {
      setLoading(true);
      const data = await api.jobs.list();
      setJobs(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch jobs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
    // Poll for updates if there are processing jobs
    const interval = setInterval(() => {
      const hasProcessing = jobs.some(j => j.status === 'processing' || j.status === 'queued');
      if (hasProcessing) {
        fetchJobs();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [jobs.length]);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Video Generation Jobs</h1>
          <p className="text-sm text-gray-500">View and manage your video generation requests</p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={fetchJobs}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            <RefreshCcw className="mr-2 h-4 w-4" />
            Refresh
          </button>
          <Link
            href="/create"
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
          >
            <Plus className="mr-2 h-4 w-4" />
            New Job
          </Link>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4">
          <div className="flex">
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {loading && jobs.length === 0 ? (
        <div className="flex justify-center py-12">
          <RefreshCcw className="h-8 w-8 text-blue-500 animate-spin" />
        </div>
      ) : jobs.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border-2 border-dashed border-gray-300">
          <p className="text-gray-500">No jobs found. Start by creating a new one!</p>
          <Link
            href="/create"
            className="mt-4 inline-flex items-center px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-500"
          >
            Create your first job
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {jobs.map((job) => (
            <JobCard key={job.id} job={job} />
          ))}
        </div>
      )}
    </div>
  );
}
