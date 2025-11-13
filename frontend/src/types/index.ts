/**
 * TypeScript type definitions for the Video Frame Person & Face Detection System
 */

export interface VideoInfo {
  name: string;
  path: string;
  size_bytes: number;
  format: string;
}

export interface FolderInfo {
  name: string;
  path: string;
  video_count: number;
}

export interface ProcessRequest {
  input_type: 'video' | 'folder';
  path: string;
  timestamps?: number[];
  frame_interval?: number;
  extract_keyframes?: boolean;
  detect_persons?: boolean;
  detect_faces?: boolean;
}

export interface JobResponse {
  job_id: string;
  status: 'processing' | 'completed' | 'failed';
  message: string;
}

export interface BoundingBox {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface PersonDetection {
  person_id: number;
  bbox: number[]; // [x, y, w, h]
  confidence: number;
  crop_path: string;
}

export interface FaceDetection {
  face_id: number;
  person_id?: number;
  bbox: number[]; // [x, y, w, h]
  confidence: number;
  landmarks: number[][];
  embedding_path: string;
  crop_path: string;
}

export interface FrameData {
  frame_id: number;
  frame_name: string;
  frame_path: string;
  timestamp: number;
  timestamp_str: string;
  video_source: string;
  video_path: string;
  persons?: PersonDetection[];
  faces?: FaceDetection[];
}

export interface JobSummary {
  job_id: string;
  input_type: string;
  input_path: string;
  status: string;
  processing_time: string;
  total_frames: number;
  persons_detected: number;
  faces_detected: number;
  output_dir: string;
}

export interface JobMetadata {
  summary: JobSummary;
  frames: FrameData[];
  person_results: any[];
  face_results: any[];
}

export interface CompareRequest {
  job_id: string;
  reference_image: string; // base64 encoded
  threshold: number;
}

export interface FaceMatch {
  rank?: number;
  face_id: string;
  frame_id: number;
  frame_name: string;
  similarity: number;
  timestamp: number;
  video_source: string;
  bbox: number[];
  crop_path: string;
}

export interface ComparisonResult {
  comparison_id?: string;
  reference_image?: string;
  threshold: number;
  status?: string;
  processing_time?: string;
  summary?: {
    total_faces_checked: number;
    matches_found: number;
    avg_similarity: number;
  };
  total_matches?: number;
  matches: FaceMatch[];
}

export interface JobInfo {
  job_id: string;
  status: 'processing' | 'completed' | 'failed';
  input_type: string;
  input_path: string;
  created_at: string;
  completed_at?: string;
  failed_at?: string;
  error?: string;
  config: ProcessRequest;
  result?: JobSummary;
}

export interface ApiError {
  detail: string;
}

export interface UploadResponse {
  message: string;
  filename: string;
  size_bytes: number;
  path: string;
}
