import Link from 'next/link';
import { Video, List, Activity, ArrowRight } from 'lucide-react';

export default function HomePage() {
  return (
    <div className="space-y-12 py-12">
      <div className="text-center">
        <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl md:text-6xl">
          <span className="block text-blue-600">AI Video Generation</span>
          <span className="block">Platform</span>
        </h1>
        <p className="mt-3 max-w-md mx-auto text-base text-gray-500 sm:text-lg md:mt-5 md:text-xl md:max-w-3xl">
          Create stunning videos from simple text prompts using multiple AI providers. Track your jobs in real-time and monitor provider performance.
        </p>
        <div className="mt-5 max-w-md mx-auto sm:flex sm:justify-center md:mt-8">
          <div className="rounded-md shadow">
            <Link
              href="/create"
              className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 md:py-4 md:text-lg md:px-10"
            >
              Start Generating
            </Link>
          </div>
          <div className="mt-3 rounded-md shadow sm:mt-0 sm:ml-3">
            <Link
              href="/jobs"
              className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-blue-600 bg-white hover:bg-gray-50 md:py-4 md:text-lg md:px-10"
            >
              View Jobs
            </Link>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
        <div className="bg-white p-6 rounded-xl shadow-md border border-gray-100">
          <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
            <Video className="h-6 w-6 text-blue-600" />
          </div>
          <h3 className="text-lg font-bold mb-2">Easy Generation</h3>
          <p className="text-gray-500 mb-4">Just enter a prompt and let our AI handle the rest. Multi-provider support ensures high availability.</p>
          <Link href="/create" className="text-blue-600 font-medium flex items-center hover:underline">
            Try it now <ArrowRight className="ml-1 h-4 w-4" />
          </Link>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-md border border-gray-100">
          <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
            <List className="h-6 w-6 text-green-600" />
          </div>
          <h3 className="text-lg font-bold mb-2">Job Tracking</h3>
          <p className="text-gray-500 mb-4">Monitor the status of your video generation jobs from queue to completion with real-time updates.</p>
          <Link href="/jobs" className="text-green-600 font-medium flex items-center hover:underline">
            Manage jobs <ArrowRight className="ml-1 h-4 w-4" />
          </Link>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-md border border-gray-100">
          <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
            <Activity className="h-6 w-6 text-purple-600" />
          </div>
          <h3 className="text-lg font-bold mb-2">Provider Health</h3>
          <p className="text-gray-500 mb-4">Transparency into our AI providers' performance, response times, and current health status.</p>
          <Link href="/providers" className="text-purple-600 font-medium flex items-center hover:underline">
            View health <ArrowRight className="ml-1 h-4 w-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}
