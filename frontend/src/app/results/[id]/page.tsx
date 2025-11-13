'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { apiClient } from '@/lib/api';
import { formatTimestamp, downloadBlob } from '@/lib/utils';
import type { JobMetadata, FrameData } from '@/types';

export default function ResultsPage() {
  const params = useParams();
  const jobId = params.id as string;

  const [metadata, setMetadata] = useState<JobMetadata | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // View options
  const [showPersons, setShowPersons] = useState(true);
  const [showFaces, setShowFaces] = useState(true);
  const [selectedFrame, setSelectedFrame] = useState<number | null>(null);

  useEffect(() => {
    loadResults();
  }, [jobId]);

  const loadResults = async () => {
    try {
      const data = await apiClient.getJobResults(jobId);
      setMetadata(data);
    } catch (err: any) {
      console.error('Failed to load results:', err);
      setError(err.message || 'Failed to load results');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadMetadata = async (fileType: 'metadata' | 'person_meta' | 'face_meta') => {
    try {
      const blob = await apiClient.downloadMetadata(jobId, fileType);
      const extension = fileType === 'metadata' ? 'json' : 'csv';
      downloadBlob(blob, `${jobId}_${fileType}.${extension}`);
    } catch (err: any) {
      alert(`Download failed: ${err.message}`);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading results...</p>
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

  if (!metadata) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
        <div className="text-center">
          <div className="text-4xl mb-4">❓</div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
            No results found
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

  const getFrameImageUrl = (frameId: number) => {
    return apiClient.getFramePreviewUrl(jobId, frameId, {
      show_persons: showPersons,
      show_faces: showFaces,
    });
  };

  return (
    <div className="space-y-6">
      {/* Header & Summary */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              Processing Results
            </h2>
            <p className="text-gray-600 dark:text-gray-400 font-mono">{jobId}</p>
          </div>
          <Link
            href={`/compare/${jobId}`}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white font-medium rounded-lg transition-colors"
          >
            🔍 Compare Faces
          </Link>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <p className="text-sm text-blue-700 dark:text-blue-400 mb-1">Total Frames</p>
            <p className="text-3xl font-bold text-blue-900 dark:text-blue-300">
              {metadata.summary.total_frames}
            </p>
          </div>
          <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-4">
            <p className="text-sm text-purple-700 dark:text-purple-400 mb-1">Persons Detected</p>
            <p className="text-3xl font-bold text-purple-900 dark:text-purple-300">
              {metadata.summary.persons_detected}
            </p>
          </div>
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
            <p className="text-sm text-green-700 dark:text-green-400 mb-1">Faces Detected</p>
            <p className="text-3xl font-bold text-green-900 dark:text-green-300">
              {metadata.summary.faces_detected}
            </p>
          </div>
        </div>

        {/* Download Options */}
        <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Download Results
          </h3>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => handleDownloadMetadata('metadata')}
              className="px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 text-sm font-medium rounded-lg transition-colors"
            >
              📄 Metadata (JSON)
            </button>
            <button
              onClick={() => handleDownloadMetadata('person_meta')}
              className="px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 text-sm font-medium rounded-lg transition-colors"
            >
              👤 Person Data (CSV)
            </button>
            <button
              onClick={() => handleDownloadMetadata('face_meta')}
              className="px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 text-sm font-medium rounded-lg transition-colors"
            >
              😊 Face Data (CSV)
            </button>
          </div>
        </div>
      </div>

      {/* View Options */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
        <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
          Display Options
        </h3>
        <div className="flex space-x-6">
          <div className="flex items-center">
            <input
              type="checkbox"
              id="showPersons"
              checked={showPersons}
              onChange={(e) => setShowPersons(e.target.checked)}
              className="mr-2 w-4 h-4"
            />
            <label htmlFor="showPersons" className="text-gray-700 dark:text-gray-300">
              Show Person Boxes (Blue)
            </label>
          </div>
          <div className="flex items-center">
            <input
              type="checkbox"
              id="showFaces"
              checked={showFaces}
              onChange={(e) => setShowFaces(e.target.checked)}
              className="mr-2 w-4 h-4"
            />
            <label htmlFor="showFaces" className="text-gray-700 dark:text-gray-300">
              Show Face Boxes (Green)
            </label>
          </div>
        </div>
      </div>

      {/* Frame Gallery */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
        <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
          Extracted Frames ({metadata.frames.length})
        </h3>

        {metadata.frames.length === 0 ? (
          <div className="text-center py-12 text-gray-600 dark:text-gray-400">
            No frames available
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {metadata.frames.map((frame) => (
              <div
                key={frame.frame_id}
                className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden hover:border-primary-500 transition-colors cursor-pointer"
                onClick={() => setSelectedFrame(frame.frame_id)}
              >
                <div className="relative aspect-video bg-gray-100 dark:bg-gray-700">
                  <img
                    src={getFrameImageUrl(frame.frame_id)}
                    alt={`Frame ${frame.frame_id}`}
                    className="w-full h-full object-contain"
                    loading="lazy"
                    onError={(e) => {
                      e.currentTarget.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="300"%3E%3Crect fill="%23ddd" width="400" height="300"/%3E%3Ctext fill="%23999" x="50%25" y="50%25" text-anchor="middle" dy=".3em"%3EFrame not available%3C/text%3E%3C/svg%3E';
                    }}
                  />
                  <div className="absolute top-2 left-2 bg-black/70 text-white px-2 py-1 rounded text-xs font-mono">
                    Frame {frame.frame_id}
                  </div>
                </div>
                <div className="p-3 bg-gray-50 dark:bg-gray-700">
                  <p className="text-sm text-gray-700 dark:text-gray-300 font-medium mb-1">
                    {frame.frame_name}
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
                    ⏱️ {formatTimestamp(frame.timestamp)}
                  </p>
                  <div className="flex justify-between text-xs">
                    <span className="text-blue-600 dark:text-blue-400">
                      👤 {frame.persons?.length || 0} persons
                    </span>
                    <span className="text-green-600 dark:text-green-400">
                      😊 {frame.faces?.length || 0} faces
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Frame Detail Modal */}
      {selectedFrame !== null && (
        <div
          className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50"
          onClick={() => setSelectedFrame(null)}
        >
          <div
            className="bg-white dark:bg-gray-800 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                  Frame {selectedFrame}
                </h3>
                <button
                  onClick={() => setSelectedFrame(null)}
                  className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white text-2xl"
                >
                  ×
                </button>
              </div>
              <img
                src={getFrameImageUrl(selectedFrame)}
                alt={`Frame ${selectedFrame}`}
                className="w-full rounded-lg mb-4"
              />
              {metadata.frames[selectedFrame] && (
                <div className="space-y-2 text-sm">
                  <p className="text-gray-700 dark:text-gray-300">
                    <strong>Name:</strong> {metadata.frames[selectedFrame].frame_name}
                  </p>
                  <p className="text-gray-700 dark:text-gray-300">
                    <strong>Timestamp:</strong> {metadata.frames[selectedFrame].timestamp_str}
                  </p>
                  <p className="text-gray-700 dark:text-gray-300">
                    <strong>Source:</strong> {metadata.frames[selectedFrame].video_source}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
