'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { ProviderHealth } from '@/types';
import { Activity, Shield, ShieldAlert, ShieldCheck, RefreshCcw, Zap } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export default function ProvidersPage() {
  const [providers, setProviders] = useState<ProviderHealth[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [testing, setTesting] = useState<string | null>(null);

  const fetchProviders = async () => {
    try {
      setLoading(true);
      const data = await api.providers.status();
      setProviders(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch provider status');
    } finally {
      setLoading(false);
    }
  };

  const testProvider = async (providerName: string) => {
    try {
      setTesting(providerName);
      await api.providers.test(providerName);
      await fetchProviders();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Test failed');
    } finally {
      setTesting(null);
    }
  };

  useEffect(() => {
    fetchProviders();
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <ShieldCheck className="h-5 w-5 text-green-500" />;
      case 'degraded':
        return <Shield className="h-5 w-5 text-yellow-500" />;
      case 'unhealthy':
        return <ShieldAlert className="h-5 w-5 text-red-500" />;
      default:
        return <Activity className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-800 bg-green-100';
      case 'degraded':
        return 'text-yellow-800 bg-yellow-100';
      case 'unhealthy':
        return 'text-red-800 bg-red-100';
      default:
        return 'text-gray-800 bg-gray-100';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI Providers</h1>
          <p className="text-sm text-gray-500">Monitor health and performance of video generation providers</p>
        </div>
        <button
          onClick={fetchProviders}
          className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
        >
          <RefreshCcw className={cn('mr-2 h-4 w-4', loading && 'animate-spin')} />
          Refresh Status
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {loading && providers.length === 0 ? (
        <div className="flex justify-center py-12">
          <RefreshCcw className="h-8 w-8 text-blue-500 animate-spin" />
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {providers.map((provider) => (
              <li key={provider.provider}>
                <div className="px-4 py-4 flex items-center justify-between sm:px-6">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">{getStatusIcon(provider.status)}</div>
                    <div className="ml-4">
                      <h4 className="text-lg font-bold text-gray-900 capitalize">{provider.provider}</h4>
                      <div className="flex items-center space-x-4 mt-1">
                        <span
                          className={cn(
                            'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                            getStatusColor(provider.status)
                          )}
                        >
                          {provider.status}
                        </span>
                        <span className="text-sm text-gray-500 flex items-center">
                          <Zap className="mr-1 h-3 w-3" />
                          {provider.avgResponseTimeMs.toFixed(0)}ms avg
                        </span>
                        <span className="text-sm text-gray-500">
                          Last check: {new Date(provider.lastCheckedAt).toLocaleTimeString()}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div>
                    <button
                      onClick={() => testProvider(provider.provider)}
                      disabled={testing === provider.provider}
                      className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-full shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                    >
                      {testing === provider.provider ? 'Testing...' : 'Test Provider'}
                    </button>
                  </div>
                </div>
              </li>
            ))}
            {providers.length === 0 && !loading && (
              <li className="px-4 py-12 text-center text-gray-500">No providers found in the database.</li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
}
