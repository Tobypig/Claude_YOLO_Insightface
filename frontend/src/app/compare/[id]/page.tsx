'use client';

import { useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { useDropzone } from 'react-dropzone';
import { apiClient } from '@/lib/api';
import { formatSimilarity, getSimilarityColor, formatTimestamp, isValidImageFile } from '@/lib/utils';
import type { ComparisonResult } from '@/types';

export default function ComparePage() {
  const params = useParams();
  const jobId = params.id as string;

  const [referenceImage, setReferenceImage] = useState<File | null>(null);
  const [referencePreview, setReferencePreview] = useState<string | null>(null);
  const [threshold, setThreshold] = useState(0.7);
  const [comparing, setComparing] = useState(false);
  const [result, setResult] = useState<ComparisonResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Handle reference image drop
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      if (isValidImageFile(file)) {
        setReferenceImage(file);

        // Create preview
        const reader = new FileReader();
        reader.onloadend = () => {
          setReferencePreview(reader.result as string);
        };
        reader.readAsDataURL(file);
      } else {
        alert('Invalid file format. Please upload JPG, JPEG, PNG, or WEBP files.');
      }
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpg', '.jpeg', '.png', '.webp']
    },
    maxFiles: 1,
    multiple: false
  });

  // Handle comparison
  const handleCompare = async () => {
    if (!referenceImage) {
      alert('Please select a reference face image');
      return;
    }

    setComparing(true);
    setError(null);

    try {
      // Convert image to base64
      const base64 = await apiClient.fileToBase64(referenceImage);

      // Perform comparison
      const comparisonResult = await apiClient.compareFaces({
        job_id: jobId,
        reference_image: base64,
        threshold: threshold,
      });

      setResult(comparisonResult);
    } catch (err: any) {
      console.error('Comparison failed:', err);
      setError(err.response?.data?.detail || err.message || 'Comparison failed');
    } finally {
      setComparing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              Face Comparison
            </h2>
            <p className="text-gray-600 dark:text-gray-400">
              Upload a reference face to find similar faces in job: <span className="font-mono">{jobId}</span>
            </p>
          </div>
          <Link
            href={`/results/${jobId}`}
            className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition-colors"
          >
            📊 View Results
          </Link>
        </div>
      </div>

      {/* Reference Image Upload */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
        <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
          1. Upload Reference Face
        </h3>

        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors mb-4 ${
            isDragActive
              ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
              : 'border-gray-300 dark:border-gray-600 hover:border-primary-400'
          }`}
        >
          <input {...getInputProps()} />
          {referencePreview ? (
            <div>
              <img
                src={referencePreview}
                alt="Reference face"
                className="max-w-xs max-h-64 mx-auto rounded-lg mb-2"
              />
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {referenceImage?.name}
              </p>
            </div>
          ) : (
            <div>
              <div className="text-4xl mb-2">🖼️</div>
              <p className="text-gray-700 dark:text-gray-300">
                {isDragActive
                  ? 'Drop the image here'
                  : 'Drag & drop a face image here, or click to select'}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
                Supported formats: JPG, PNG, WEBP
              </p>
            </div>
          )}
        </div>

        {/* Threshold Setting */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            2. Similarity Threshold: {formatSimilarity(threshold)}
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={threshold}
            onChange={(e) => setThreshold(parseFloat(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400 mt-1">
            <span>More matches (0%)</span>
            <span>Exact matches (100%)</span>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
            Higher threshold = stricter matching (fewer false positives)
          </p>
        </div>

        {/* Compare Button */}
        <button
          onClick={handleCompare}
          disabled={!referenceImage || comparing}
          className={`w-full mt-6 py-3 rounded-lg font-bold text-white transition-colors ${
            !referenceImage || comparing
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-green-600 hover:bg-green-700'
          }`}
        >
          {comparing ? 'Comparing...' : '3. Compare Faces'}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <h4 className="text-lg font-bold text-red-900 dark:text-red-300 mb-2">
              ✗ Comparison Failed
            </h4>
            <p className="text-red-700 dark:text-red-400">{error}</p>
          </div>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
          <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
            Comparison Results
          </h3>

          {/* Summary */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <p className="text-sm text-blue-700 dark:text-blue-400 mb-1">Faces Checked</p>
              <p className="text-2xl font-bold text-blue-900 dark:text-blue-300">
                {result.summary?.total_faces_checked || 0}
              </p>
            </div>
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
              <p className="text-sm text-green-700 dark:text-green-400 mb-1">Matches Found</p>
              <p className="text-2xl font-bold text-green-900 dark:text-green-300">
                {result.matches.length}
              </p>
            </div>
            <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-4">
              <p className="text-sm text-purple-700 dark:text-purple-400 mb-1">Avg Similarity</p>
              <p className="text-2xl font-bold text-purple-900 dark:text-purple-300">
                {result.summary?.avg_similarity
                  ? formatSimilarity(result.summary.avg_similarity)
                  : 'N/A'}
              </p>
            </div>
          </div>

          {/* Matches */}
          {result.matches.length === 0 ? (
            <div className="text-center py-12 text-gray-600 dark:text-gray-400">
              <div className="text-4xl mb-4">🔍</div>
              <h4 className="text-xl font-semibold mb-2">No matches found</h4>
              <p>Try lowering the similarity threshold to find more matches</p>
            </div>
          ) : (
            <div>
              <h4 className="text-md font-semibold text-gray-900 dark:text-white mb-3">
                Matching Faces (sorted by similarity)
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {result.matches.map((match, index) => (
                  <div
                    key={`${match.frame_id}-${match.face_id}`}
                    className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
                  >
                    <div className="relative aspect-square bg-gray-100 dark:bg-gray-700">
                      <div className="absolute top-2 left-2 bg-black/70 text-white px-2 py-1 rounded text-xs font-bold">
                        #{index + 1}
                      </div>
                      <div className={`absolute top-2 right-2 px-2 py-1 rounded text-xs font-bold ${
                        match.similarity >= 0.8
                          ? 'bg-green-500 text-white'
                          : match.similarity >= 0.6
                          ? 'bg-yellow-500 text-black'
                          : 'bg-red-500 text-white'
                      }`}>
                        {formatSimilarity(match.similarity)}
                      </div>
                      {/* Note: In production, you'd display the actual face crop image */}
                      <div className="w-full h-full flex items-center justify-center text-gray-400">
                        <div className="text-center">
                          <div className="text-4xl mb-2">😊</div>
                          <p className="text-sm">Face {match.face_id}</p>
                        </div>
                      </div>
                    </div>
                    <div className="p-3 bg-gray-50 dark:bg-gray-700">
                      <p className="text-sm text-gray-700 dark:text-gray-300 font-medium mb-1">
                        Frame {match.frame_id}: {match.frame_name}
                      </p>
                      <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
                        ⏱️ {formatTimestamp(match.timestamp)}
                      </p>
                      {match.video_source && (
                        <p className="text-xs text-gray-600 dark:text-gray-400 truncate">
                          📹 {match.video_source}
                        </p>
                      )}
                      <div className="mt-2">
                        <span className={`text-sm font-bold ${getSimilarityColor(match.similarity)}`}>
                          Similarity: {formatSimilarity(match.similarity)}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tips */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
        <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-3">
          💡 Tips for Better Results
        </h3>
        <ul className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
          <li>✓ Use clear, front-facing photos of the person</li>
          <li>✓ Ensure good lighting and minimal obstructions</li>
          <li>✓ Higher threshold (0.7-0.9) = more accurate but fewer matches</li>
          <li>✓ Lower threshold (0.5-0.7) = more matches but may include false positives</li>
          <li>✓ The system uses 512-dimensional face embeddings for comparison</li>
        </ul>
      </div>
    </div>
  );
}
