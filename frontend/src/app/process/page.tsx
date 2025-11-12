'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useDropzone } from 'react-dropzone';
import { apiClient } from '@/lib/api';
import { formatBytes, isValidVideoFile } from '@/lib/utils';
import type { VideoInfo, FolderInfo, ProcessRequest } from '@/types';

export default function ProcessPage() {
  const router = useRouter();
  const [inputType, setInputType] = useState<'upload' | 'library' | 'folder'>('upload');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedVideo, setSelectedVideo] = useState<string>('');
  const [selectedFolder, setSelectedFolder] = useState<string>('');
  const [videos, setVideos] = useState<VideoInfo[]>([]);
  const [folders, setFolders] = useState<FolderInfo[]>([]);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);

  // Processing configuration
  const [timestampMode, setTimestampMode] = useState<'manual' | 'interval' | 'keyframes'>('interval');
  const [timestamps, setTimestamps] = useState<string>('');
  const [frameInterval, setFrameInterval] = useState<number>(5);
  const [detectPersons, setDetectPersons] = useState(true);
  const [detectFaces, setDetectFaces] = useState(true);

  // Load videos and folders
  const loadVideos = async () => {
    try {
      const data = await apiClient.listVideos();
      setVideos(data);
    } catch (error) {
      console.error('Failed to load videos:', error);
    }
  };

  const loadFolders = async () => {
    try {
      const data = await apiClient.listFolders();
      setFolders(data);
    } catch (error) {
      console.error('Failed to load folders:', error);
    }
  };

  // Handle file drop
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      if (isValidVideoFile(file)) {
        setSelectedFile(file);
      } else {
        alert('Invalid file format. Please upload MP4, MOV, AVI, or MKV files.');
      }
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'video/*': ['.mp4', '.mov', '.avi', '.mkv']
    },
    maxFiles: 1,
    multiple: false
  });

  // Handle video upload
  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    try {
      const response = await apiClient.uploadVideo(selectedFile, setUploadProgress);
      alert(`Video uploaded successfully: ${response.filename}`);
      setSelectedVideo(response.path);
      setInputType('library');
      await loadVideos();
    } catch (error: any) {
      console.error('Upload failed:', error);
      alert(`Upload failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  // Handle process start
  const handleProcess = async () => {
    // Validate input
    let inputPath = '';
    let processInputType: 'video' | 'folder' = 'video';

    if (inputType === 'upload' && !selectedFile) {
      alert('Please select a video file');
      return;
    }

    if (inputType === 'upload') {
      // Upload first
      await handleUpload();
      if (!selectedVideo) {
        alert('Failed to upload video');
        return;
      }
      inputPath = selectedVideo;
    } else if (inputType === 'library') {
      if (!selectedVideo) {
        alert('Please select a video from the library');
        return;
      }
      inputPath = selectedVideo;
    } else if (inputType === 'folder') {
      if (!selectedFolder) {
        alert('Please select a folder');
        return;
      }
      inputPath = selectedFolder;
      processInputType = 'folder';
    }

    // Build request
    const request: ProcessRequest = {
      input_type: processInputType,
      path: inputPath,
      detect_persons: detectPersons,
      detect_faces: detectFaces,
    };

    // Add timestamp configuration
    if (timestampMode === 'manual') {
      const timestampList = timestamps
        .split(',')
        .map(t => parseFloat(t.trim()))
        .filter(t => !isNaN(t));
      if (timestampList.length === 0) {
        alert('Please enter valid timestamps (comma-separated numbers)');
        return;
      }
      request.timestamps = timestampList;
    } else if (timestampMode === 'interval') {
      request.frame_interval = frameInterval;
    } else if (timestampMode === 'keyframes') {
      request.extract_keyframes = true;
    }

    // Start processing
    setProcessing(true);
    try {
      const response = await apiClient.processVideo(request);
      alert(`Processing started! Job ID: ${response.job_id}`);
      router.push(`/jobs/${response.job_id}`);
    } catch (error: any) {
      console.error('Processing failed:', error);
      alert(`Processing failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
          Process Video
        </h2>

        {/* Input Type Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Input Source
          </label>
          <div className="flex space-x-4">
            <button
              onClick={() => setInputType('upload')}
              className={`px-4 py-2 rounded-lg font-medium ${
                inputType === 'upload'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
              }`}
            >
              Upload Video
            </button>
            <button
              onClick={() => {
                setInputType('library');
                loadVideos();
              }}
              className={`px-4 py-2 rounded-lg font-medium ${
                inputType === 'library'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
              }`}
            >
              Video Library
            </button>
            <button
              onClick={() => {
                setInputType('folder');
                loadFolders();
              }}
              className={`px-4 py-2 rounded-lg font-medium ${
                inputType === 'folder'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
              }`}
            >
              Video Folder
            </button>
          </div>
        </div>

        {/* Upload Section */}
        {inputType === 'upload' && (
          <div className="mb-6">
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                isDragActive
                  ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                  : 'border-gray-300 dark:border-gray-600 hover:border-primary-400'
              }`}
            >
              <input {...getInputProps()} />
              <div className="text-4xl mb-2">📁</div>
              {selectedFile ? (
                <div>
                  <p className="text-lg font-medium text-gray-900 dark:text-white">
                    {selectedFile.name}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {formatBytes(selectedFile.size)}
                  </p>
                </div>
              ) : (
                <div>
                  <p className="text-gray-700 dark:text-gray-300">
                    {isDragActive
                      ? 'Drop the video file here'
                      : 'Drag & drop a video file here, or click to select'}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
                    Supported formats: MP4, MOV, AVI, MKV
                  </p>
                </div>
              )}
            </div>

            {uploading && (
              <div className="mt-4">
                <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-1">
                  <span>Uploading...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-primary-600 h-2 rounded-full transition-all"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {/* Video Library */}
        {inputType === 'library' && (
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Select Video
            </label>
            <select
              value={selectedVideo}
              onChange={(e) => setSelectedVideo(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="">-- Select a video --</option>
              {videos.map((video) => (
                <option key={video.path} value={video.path}>
                  {video.name} ({formatBytes(video.size_bytes)})
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Folder Selection */}
        {inputType === 'folder' && (
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Select Folder
            </label>
            <select
              value={selectedFolder}
              onChange={(e) => setSelectedFolder(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="">-- Select a folder --</option>
              {folders.map((folder) => (
                <option key={folder.path} value={folder.path}>
                  {folder.name} ({folder.video_count} videos)
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Frame Extraction Settings */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Frame Extraction Mode
          </label>
          <div className="space-y-3">
            <div className="flex items-center">
              <input
                type="radio"
                id="interval"
                checked={timestampMode === 'interval'}
                onChange={() => setTimestampMode('interval')}
                className="mr-2"
              />
              <label htmlFor="interval" className="text-gray-700 dark:text-gray-300">
                Regular Interval
              </label>
            </div>
            {timestampMode === 'interval' && (
              <div className="ml-6">
                <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">
                  Interval (seconds)
                </label>
                <input
                  type="number"
                  value={frameInterval}
                  onChange={(e) => setFrameInterval(parseFloat(e.target.value))}
                  min="0.1"
                  step="0.5"
                  className="w-32 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
            )}

            <div className="flex items-center">
              <input
                type="radio"
                id="manual"
                checked={timestampMode === 'manual'}
                onChange={() => setTimestampMode('manual')}
                className="mr-2"
              />
              <label htmlFor="manual" className="text-gray-700 dark:text-gray-300">
                Specific Timestamps
              </label>
            </div>
            {timestampMode === 'manual' && (
              <div className="ml-6">
                <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">
                  Timestamps (comma-separated seconds)
                </label>
                <input
                  type="text"
                  value={timestamps}
                  onChange={(e) => setTimestamps(e.target.value)}
                  placeholder="e.g., 10, 25.5, 60, 120"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
            )}

            <div className="flex items-center">
              <input
                type="radio"
                id="keyframes"
                checked={timestampMode === 'keyframes'}
                onChange={() => setTimestampMode('keyframes')}
                className="mr-2"
              />
              <label htmlFor="keyframes" className="text-gray-700 dark:text-gray-300">
                Key Frames (scene changes)
              </label>
            </div>
          </div>
        </div>

        {/* Detection Options */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Detection Options
          </label>
          <div className="space-y-2">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="detectPersons"
                checked={detectPersons}
                onChange={(e) => setDetectPersons(e.target.checked)}
                className="mr-2"
              />
              <label htmlFor="detectPersons" className="text-gray-700 dark:text-gray-300">
                Enable Person Detection (YOLO)
              </label>
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                id="detectFaces"
                checked={detectFaces}
                onChange={(e) => setDetectFaces(e.target.checked)}
                className="mr-2"
              />
              <label htmlFor="detectFaces" className="text-gray-700 dark:text-gray-300">
                Enable Face Detection (InsightFace)
              </label>
            </div>
          </div>
        </div>

        {/* Process Button */}
        <button
          onClick={handleProcess}
          disabled={processing || uploading}
          className={`w-full py-3 rounded-lg font-bold text-white transition-colors ${
            processing || uploading
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-primary-600 hover:bg-primary-700'
          }`}
        >
          {processing ? 'Processing...' : uploading ? 'Uploading...' : 'Start Processing'}
        </button>
      </div>
    </div>
  );
}
