'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/app/providers/auth-provider';
import { jobsApi } from '@/services/api';
import { Loader2, Video } from 'lucide-react';

export default function CreateJobPage() {
  const router = useRouter();
  const { isAuthenticated, user } = useAuth();
  const [prompt, setPrompt] = useState('');
  const [model, setModel] = useState('');
  const [resolution, setResolution] = useState('1080p');
  const [quality, setQuality] = useState('high');
  const [duration, setDuration] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    if (!isAuthenticated) {
      setError('Please log in to create a job');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      await jobsApi.create({
        prompt,
        model: model || undefined,
        resolution,
        quality,
        duration: duration || undefined,
        maxRetries: 3,
      });
      router.push('/jobs');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create job');
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white shadow sm:rounded-lg overflow-hidden">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 flex items-center">
            <Video className="mr-2 h-5 w-5 text-blue-500" />
            Create Video Generation Job
          </h3>
          <div className="mt-2 max-w-xl text-sm text-gray-500">
            <p>Enter a prompt and we'll use our AI providers to generate a video for you.</p>
          </div>
          <form onSubmit={handleSubmit} className="mt-5 space-y-4">
            <div>
              <label htmlFor="prompt" className="block text-sm font-medium text-gray-700">
                Prompt
              </label>
              <textarea
                id="prompt"
                name="prompt"
                rows={4}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="A futuristic city with flying cars at night, neon lights..."
                required
              />
            </div>

            <div>
              <label htmlFor="model" className="block text-sm font-medium text-gray-700">
                AI Model (optional)
              </label>
              <input
                type="text"
                id="model"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="e.g., gpt-4, claude-3"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="resolution" className="block text-sm font-medium text-gray-700">
                  Resolution
                </label>
                <select
                  id="resolution"
                  value={resolution}
                  onChange={(e) => setResolution(e.target.value)}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                >
                  <option value="4k">4K</option>
                  <option value="1080p">1080p</option>
                  <option value="720p">720p</option>
                  <option value="480p">480p</option>
                </select>
              </div>

              <div>
                <label htmlFor="quality" className="block text-sm font-medium text-gray-700">
                  Quality
                </label>
                <select
                  id="quality"
                  value={quality}
                  onChange={(e) => setQuality(e.target.value)}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                >
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
            </div>

            <div>
              <label htmlFor="duration" className="block text-sm font-medium text-gray-700">
                Duration (seconds, optional)
              </label>
              <input
                type="number"
                id="duration"
                min="1"
                max="60"
                value={duration || ''}
                onChange={(e) => setDuration(e.target.value ? parseInt(e.target.value) : null)}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="e.g., 10"
              />
            </div>

            {error && (
              <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
                {error}
              </div>
            )}

            <div className="flex justify-end">
              <button
                type="button"
                onClick={() => router.back()}
                className="mr-3 bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading || !prompt.trim()}
                className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <Loader2 className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" />
                    Creating...
                  </>
                ) : (
                  'Generate Video'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
