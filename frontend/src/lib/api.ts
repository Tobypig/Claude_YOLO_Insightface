/**
 * API client for communicating with the backend
 */
import axios, { AxiosInstance } from 'axios';
import type {
  VideoInfo,
  FolderInfo,
  ProcessRequest,
  JobResponse,
  JobInfo,
  JobMetadata,
  CompareRequest,
  ComparisonResult,
  UploadResponse,
} from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private client: AxiosInstance;

  constructor(baseURL: string = API_BASE_URL) {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 300000, // 5 minutes for long-running operations
    });
  }

  // Health check
  async healthCheck() {
    const response = await this.client.get('/api/health');
    return response.data;
  }

  // List videos
  async listVideos(): Promise<VideoInfo[]> {
    const response = await this.client.get<VideoInfo[]>('/api/videos');
    return response.data;
  }

  // List folders
  async listFolders(): Promise<FolderInfo[]> {
    const response = await this.client.get<FolderInfo[]>('/api/folders');
    return response.data;
  }

  // Upload video
  async uploadVideo(file: File, onProgress?: (progress: number) => void): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.client.post<UploadResponse>('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percentCompleted);
        }
      },
    });

    return response.data;
  }

  // Process video or folder
  async processVideo(request: ProcessRequest): Promise<JobResponse> {
    const response = await this.client.post<JobResponse>('/api/process', request);
    return response.data;
  }

  // Get job status
  async getJobStatus(jobId: string): Promise<JobInfo> {
    const response = await this.client.get<JobInfo>(`/api/jobs/${jobId}`);
    return response.data;
  }

  // Get job results
  async getJobResults(jobId: string): Promise<JobMetadata> {
    const response = await this.client.get<JobMetadata>(`/api/results/${jobId}`);
    return response.data;
  }

  // Get frame preview
  getFramePreviewUrl(
    jobId: string,
    frameId: number,
    options?: {
      show_persons?: boolean;
      show_faces?: boolean;
      person_threshold?: number;
      face_threshold?: number;
    }
  ): string {
    const params = new URLSearchParams();

    if (options?.show_persons !== undefined) {
      params.append('show_persons', String(options.show_persons));
    }
    if (options?.show_faces !== undefined) {
      params.append('show_faces', String(options.show_faces));
    }
    if (options?.person_threshold !== undefined) {
      params.append('person_threshold', String(options.person_threshold));
    }
    if (options?.face_threshold !== undefined) {
      params.append('face_threshold', String(options.face_threshold));
    }

    const queryString = params.toString();
    const url = `${API_BASE_URL}/api/preview/${jobId}/frame/${frameId}`;

    return queryString ? `${url}?${queryString}` : url;
  }

  // Compare faces
  async compareFaces(request: CompareRequest): Promise<ComparisonResult> {
    const response = await this.client.post<ComparisonResult>('/api/compare', request);
    return response.data;
  }

  // Download metadata
  async downloadMetadata(jobId: string, fileType: 'metadata' | 'person_meta' | 'face_meta'): Promise<Blob> {
    const response = await this.client.get(`/api/download/${jobId}/${fileType}`, {
      responseType: 'blob',
    });
    return response.data;
  }

  // Delete job
  async deleteJob(jobId: string): Promise<{ message: string; job_id: string }> {
    const response = await this.client.delete(`/api/jobs/${jobId}`);
    return response.data;
  }

  // Convert image to base64
  async fileToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        if (typeof reader.result === 'string') {
          // Remove data URL prefix
          const base64 = reader.result.split(',')[1];
          resolve(base64);
        } else {
          reject(new Error('Failed to convert file to base64'));
        }
      };
      reader.onerror = reject;
    });
  }

  // Poll job status until completion
  async pollJobStatus(
    jobId: string,
    onProgress?: (status: JobInfo) => void,
    interval: number = 2000,
    maxAttempts: number = 150
  ): Promise<JobInfo> {
    let attempts = 0;

    while (attempts < maxAttempts) {
      const status = await this.getJobStatus(jobId);

      if (onProgress) {
        onProgress(status);
      }

      if (status.status === 'completed' || status.status === 'failed') {
        return status;
      }

      await new Promise(resolve => setTimeout(resolve, interval));
      attempts++;
    }

    throw new Error('Job polling timeout');
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

export default ApiClient;
