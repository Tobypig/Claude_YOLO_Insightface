'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { apiClient } from '@/lib/api';

export default function Home() {
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      const response = await apiClient.healthCheck();
      setHealth(response);
    } catch (error) {
      console.error('Health check failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-8">
        <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
          Welcome to Video Face Detection System
        </h2>
        <p className="text-lg text-gray-700 dark:text-gray-300 mb-6">
          A comprehensive web-based system for extracting still frames from videos,
          detecting persons using YOLO, and performing face detection and recognition
          with InsightFace (ArcFace buffalo_l).
        </p>

        {/* System Status */}
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            System Status
          </h3>
          {loading ? (
            <p className="text-gray-600 dark:text-gray-400">Checking...</p>
          ) : health ? (
            <div className="space-y-2">
              <p className="text-green-600 dark:text-green-400 font-medium">
                ✓ Backend API is running
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Device: <span className="font-mono">{health.device}</span>
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                YOLO Model: <span className="font-mono">{health.models?.yolo}</span>
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                InsightFace Model: <span className="font-mono">{health.models?.insightface}</span>
              </p>
            </div>
          ) : (
            <p className="text-red-600 dark:text-red-400 font-medium">
              ✗ Backend API is offline
            </p>
          )}
        </div>

        <Link
          href="/process"
          className="inline-block bg-primary-600 hover:bg-primary-700 text-white font-bold py-3 px-8 rounded-lg transition-colors"
        >
          Start Processing
        </Link>
      </div>

      {/* Features */}
      <div className="grid md:grid-cols-3 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
          <div className="text-4xl mb-4">🎬</div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
            Frame Extraction
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Extract still frames from videos at specified timestamps or intervals
            using ffmpeg.
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
          <div className="text-4xl mb-4">👤</div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
            Person Detection
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Detect persons in frames using YOLOv8 with adjustable confidence
            thresholds.
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
          <div className="text-4xl mb-4">😊</div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
            Face Recognition
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Detect and recognize faces using InsightFace with 512-dim embedding
            extraction.
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
          <div className="text-4xl mb-4">📊</div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
            Interactive Preview
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            View detection results with overlaid bounding boxes and adjustable
            thresholds.
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
          <div className="text-4xl mb-4">🔍</div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
            Face Comparison
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Compare reference faces against detected faces with similarity scoring.
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
          <div className="text-4xl mb-4">📁</div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
            Batch Processing
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Process entire folders of video clips with automatic detection pipeline.
          </p>
        </div>
      </div>

      {/* Quick Start */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-8">
        <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          Quick Start Guide
        </h3>
        <ol className="list-decimal list-inside space-y-3 text-gray-700 dark:text-gray-300">
          <li>
            <strong>Upload or Select Video:</strong> Choose a video file or select
            from existing videos.
          </li>
          <li>
            <strong>Configure Processing:</strong> Set timestamps, intervals, and
            enable detection options.
          </li>
          <li>
            <strong>Process:</strong> Start the processing pipeline and wait for
            completion.
          </li>
          <li>
            <strong>Review Results:</strong> View extracted frames with detection
            overlays.
          </li>
          <li>
            <strong>Compare Faces:</strong> Upload a reference face to find matches
            (optional).
          </li>
          <li>
            <strong>Export:</strong> Download metadata, crops, and embeddings.
          </li>
        </ol>
      </div>
    </div>
  );
}
