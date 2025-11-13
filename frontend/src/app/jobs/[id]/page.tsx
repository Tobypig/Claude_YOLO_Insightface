'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { apiClient } from '@/lib/api';
import type { JobInfo } from '@/types';

export default function JobDetailPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.id as string;

  const [job, setJob] = useState<JobInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (jobId) {
      pollJobStatus();
    }
  }, [jobId]);

  const pollJobStatus = async () => {
    try {
      const status = await apiClient.pollJobStatus(
        jobId,
        (currentStatus) => {
          setJob(currentStatus);
        },
        2000, // Poll every 2 seconds
        150 // Max 5 minutes
      );
      setJob(status);
    } catch (err: any) {
      console.error('Failed to get job status:', err);
      setError(err.message || 'Failed to load job status');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this job?')) return;

    try {
      await apiClient.deleteJob(jobId);
      alert('Job deleted successfully');
      router.push('/jobs');
    } catch (err: any) {
      alert(`Failed to delete job: ${err.message}`);
    }
  };

  if (loading && !job) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading job status...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
        <div className="text-center text-red-600 dark:text-red-400">
          <div className="text-4xl mb-4">❌</div>
          <h3 className="text-xl font-bold mb-2">Error</h3>
          <p>{error}</p>
          <Link
            href="/jobs"
            className="inline-block mt-4 px-6 py-2 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition-colors"
          >
            Back to Jobs
          </Link>
        </div>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
        <div className="text-center">
          <div className="text-4xl mb-4">❓</div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
            Job not found
          </h3>
          <Link
            href="/jobs"
            className="inline-block mt-4 px-6 py-2 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition-colors"
          >
            Back to Jobs
          </Link>
        </div>
      </div>
    );
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return '✅';
      case 'processing':
        return '⏳';
      case 'failed':
        return '❌';
      default:
        return '⚪';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 dark:text-green-400';
      case 'processing':
        return 'text-blue-600 dark:text-blue-400';
      case 'failed':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              Job Details
            </h2>
            <p className="text-gray-600 dark:text-gray-400 font-mono">{jobId}</p>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={pollJobStatus}
              className="px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 font-medium rounded-lg transition-colors"
            >
              🔄 Refresh
            </button>
            <button
              onClick={handleDelete}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-colors"
            >
              🗑️ Delete
            </button>
          </div>
        </div>

        {/* Status */}
        <div className="mb-6">
          <div className={`text-4xl mb-2 ${getStatusColor(job.status)}`}>
            {getStatusIcon(job.status)}
          </div>
          <h3 className={`text-xl font-bold ${getStatusColor(job.status)}`}>
            Status: {job.status.toUpperCase()}
          </h3>
        </div>

        {/* Job Info Grid */}
        <div className="grid md:grid-cols-2 gap-4">
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
              Input Type
            </h4>
            <p className="text-lg font-semibold text-gray-900 dark:text-white">
              {job.input_type}
            </p>
          </div>

          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
              Input Path
            </h4>
            <p className="text-lg font-semibold text-gray-900 dark:text-white truncate">
              {job.input_path}
            </p>
          </div>

          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
              Created At
            </h4>
            <p className="text-lg font-semibold text-gray-900 dark:text-white">
              {new Date(job.created_at).toLocaleString()}
            </p>
          </div>

          {job.completed_at && (
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
                Completed At
              </h4>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                {new Date(job.completed_at).toLocaleString()}
              </p>
            </div>
          )}
        </div>

        {/* Processing indicator */}
        {job.status === 'processing' && (
          <div className="mt-6">
            <div className="flex items-center space-x-3 mb-2">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600"></div>
              <span className="text-gray-700 dark:text-gray-300">Processing...</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div className="bg-primary-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
            </div>
          </div>
        )}

        {/* Results Summary */}
        {job.status === 'completed' && job.result && (
          <div className="mt-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
            <h4 className="text-lg font-bold text-green-900 dark:text-green-300 mb-3">
              ✓ Processing Complete
            </h4>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-green-700 dark:text-green-400">Total Frames</p>
                <p className="text-2xl font-bold text-green-900 dark:text-green-300">
                  {job.result.total_frames}
                </p>
              </div>
              <div>
                <p className="text-sm text-green-700 dark:text-green-400">Persons Detected</p>
                <p className="text-2xl font-bold text-green-900 dark:text-green-300">
                  {job.result.persons_detected}
                </p>
              </div>
              <div>
                <p className="text-sm text-green-700 dark:text-green-400">Faces Detected</p>
                <p className="text-2xl font-bold text-green-900 dark:text-green-300">
                  {job.result.faces_detected}
                </p>
              </div>
            </div>
            <p className="text-sm text-green-700 dark:text-green-400 mt-3">
              Processing Time: {job.result.processing_time}
            </p>
          </div>
        )}

        {/* Error Message */}
        {job.status === 'failed' && job.error && (
          <div className="mt-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <h4 className="text-lg font-bold text-red-900 dark:text-red-300 mb-2">
              ✗ Processing Failed
            </h4>
            <p className="text-red-700 dark:text-red-400">{job.error}</p>
          </div>
        )}

        {/* Actions */}
        {job.status === 'completed' && (
          <div className="mt-6 flex space-x-3">
            <Link
              href={`/results/${jobId}`}
              className="flex-1 py-3 bg-primary-600 hover:bg-primary-700 text-white font-bold text-center rounded-lg transition-colors"
            >
              📊 View Results
            </Link>
            <Link
              href={`/compare/${jobId}`}
              className="flex-1 py-3 bg-green-600 hover:bg-green-700 text-white font-bold text-center rounded-lg transition-colors"
            >
              🔍 Compare Faces
            </Link>
          </div>
        )}
      </div>

      {/* Configuration Details */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
        <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
          Configuration
        </h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600 dark:text-gray-400">Person Detection:</span>
            <span className="font-medium text-gray-900 dark:text-white">
              {job.config.detect_persons ? '✓ Enabled' : '✗ Disabled'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600 dark:text-gray-400">Face Detection:</span>
            <span className="font-medium text-gray-900 dark:text-white">
              {job.config.detect_faces ? '✓ Enabled' : '✗ Disabled'}
            </span>
          </div>
          {job.config.timestamps && (
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Timestamps:</span>
              <span className="font-medium text-gray-900 dark:text-white">
                {job.config.timestamps.join(', ')}s
              </span>
            </div>
          )}
          {job.config.frame_interval && (
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Frame Interval:</span>
              <span className="font-medium text-gray-900 dark:text-white">
                {job.config.frame_interval}s
              </span>
            </div>
          )}
          {job.config.extract_keyframes && (
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Key Frames:</span>
              <span className="font-medium text-gray-900 dark:text-white">✓ Enabled</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
