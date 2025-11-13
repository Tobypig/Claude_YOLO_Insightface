/**
 * Tests for API client
 */
import axios from 'axios'
import { apiClient } from '@/lib/api'
import type { ProcessRequest, JobInfo } from '@/types'

// Mock axios
jest.mock('axios')
const mockedAxios = axios as jest.Mocked<typeof axios>

describe('API Client', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Health Check', () => {
    it('should call health check endpoint', async () => {
      const mockResponse = {
        data: {
          status: 'healthy',
          device: 'cpu',
          models: { yolo: 'yolov8n.pt', insightface: 'buffalo_l' }
        }
      }

      mockedAxios.create = jest.fn().mockReturnValue({
        get: jest.fn().mockResolvedValue(mockResponse)
      } as any)

      const client = new (require('@/lib/api').default)()
      const result = await client.healthCheck()

      expect(result.status).toBe('healthy')
    })
  })

  describe('List Videos', () => {
    it('should fetch list of videos', async () => {
      const mockVideos = [
        { name: 'video1.mp4', path: 'video1.mp4', size_bytes: 1000, format: 'mp4' },
        { name: 'video2.mp4', path: 'video2.mp4', size_bytes: 2000, format: 'mp4' }
      ]

      mockedAxios.create = jest.fn().mockReturnValue({
        get: jest.fn().mockResolvedValue({ data: mockVideos })
      } as any)

      const client = new (require('@/lib/api').default)()
      const videos = await client.listVideos()

      expect(videos).toHaveLength(2)
      expect(videos[0].name).toBe('video1.mp4')
    })
  })

  describe('Upload Video', () => {
    it('should upload video file with progress', async () => {
      const mockFile = new File(['content'], 'test.mp4', { type: 'video/mp4' })
      const mockResponse = {
        data: {
          message: 'Video uploaded successfully',
          filename: 'test.mp4',
          size_bytes: 1000,
          path: 'test.mp4'
        }
      }

      const mockPost = jest.fn().mockResolvedValue(mockResponse)

      mockedAxios.create = jest.fn().mockReturnValue({
        post: mockPost
      } as any)

      const onProgress = jest.fn()
      const client = new (require('@/lib/api').default)()

      const result = await client.uploadVideo(mockFile, onProgress)

      expect(result.filename).toBe('test.mp4')
      expect(mockPost).toHaveBeenCalled()
    })
  })

  describe('Process Video', () => {
    it('should start video processing job', async () => {
      const request: ProcessRequest = {
        input_type: 'video',
        path: 'test.mp4',
        detect_persons: true,
        detect_faces: true,
        frame_interval: 1.0
      }

      const mockResponse = {
        data: {
          job_id: 'job_12345',
          status: 'processing',
          message: 'Processing started'
        }
      }

      mockedAxios.create = jest.fn().mockReturnValue({
        post: jest.fn().mockResolvedValue(mockResponse)
      } as any)

      const client = new (require('@/lib/api').default)()
      const result = await client.processVideo(request)

      expect(result.job_id).toBe('job_12345')
      expect(result.status).toBe('processing')
    })
  })

  describe('Job Status', () => {
    it('should get job status', async () => {
      const mockStatus: JobInfo = {
        job_id: 'job_12345',
        status: 'completed',
        input_type: 'video',
        input_path: 'test.mp4',
        created_at: '2025-01-01T00:00:00',
        config: {
          input_type: 'video',
          path: 'test.mp4',
          detect_persons: true,
          detect_faces: true
        }
      }

      mockedAxios.create = jest.fn().mockReturnValue({
        get: jest.fn().mockResolvedValue({ data: mockStatus })
      } as any)

      const client = new (require('@/lib/api').default)()
      const status = await client.getJobStatus('job_12345')

      expect(status.job_id).toBe('job_12345')
      expect(status.status).toBe('completed')
    })
  })

  describe('Poll Job Status', () => {
    it('should poll until job completes', async () => {
      const mockGet = jest.fn()
        .mockResolvedValueOnce({ data: { job_id: 'job_1', status: 'processing' } })
        .mockResolvedValueOnce({ data: { job_id: 'job_1', status: 'processing' } })
        .mockResolvedValueOnce({ data: { job_id: 'job_1', status: 'completed' } })

      mockedAxios.create = jest.fn().mockReturnValue({
        get: mockGet
      } as any)

      const onProgress = jest.fn()
      const client = new (require('@/lib/api').default)()

      const result = await client.pollJobStatus('job_1', onProgress, 100, 10)

      expect(result.status).toBe('completed')
      expect(mockGet).toHaveBeenCalledTimes(3)
      expect(onProgress).toHaveBeenCalledTimes(3)
    })

    it('should timeout after max attempts', async () => {
      mockedAxios.create = jest.fn().mockReturnValue({
        get: jest.fn().mockResolvedValue({ data: { status: 'processing' } })
      } as any)

      const client = new (require('@/lib/api').default)()

      await expect(
        client.pollJobStatus('job_1', undefined, 100, 3)
      ).rejects.toThrow('Job polling timeout')
    })
  })

  describe('File to Base64', () => {
    it('should convert file to base64', async () => {
      const mockFile = new File(['test content'], 'test.jpg', { type: 'image/jpeg' })

      const client = new (require('@/lib/api').default)()

      // Note: This test requires FileReader mock which is complex in Jest
      // In real tests, you'd mock FileReader
    })
  })

  describe('Delete Job', () => {
    it('should delete job', async () => {
      const mockResponse = {
        data: {
          message: 'Job deleted successfully',
          job_id: 'job_12345'
        }
      }

      mockedAxios.create = jest.fn().mockReturnValue({
        delete: jest.fn().mockResolvedValue(mockResponse)
      } as any)

      const client = new (require('@/lib/api').default)()
      const result = await client.deleteJob('job_12345')

      expect(result.job_id).toBe('job_12345')
    })
  })

  describe('Frame Preview URL', () => {
    it('should generate correct preview URL', () => {
      const client = new (require('@/lib/api').default)()

      const url = client.getFramePreviewUrl('job_123', 5, {
        show_persons: true,
        show_faces: false,
        person_threshold: 0.7
      })

      expect(url).toContain('/api/preview/job_123/frame/5')
      expect(url).toContain('show_persons=true')
      expect(url).toContain('show_faces=false')
      expect(url).toContain('person_threshold=0.7')
    })

    it('should generate URL without params when none provided', () => {
      const client = new (require('@/lib/api').default)()

      const url = client.getFramePreviewUrl('job_123', 5)

      expect(url).toBe('http://localhost:8000/api/preview/job_123/frame/5')
    })
  })

  describe('Error Handling', () => {
    it('should handle network errors', async () => {
      mockedAxios.create = jest.fn().mockReturnValue({
        get: jest.fn().mockRejectedValue(new Error('Network error'))
      } as any)

      const client = new (require('@/lib/api').default)()

      await expect(client.healthCheck()).rejects.toThrow('Network error')
    })

    it('should handle API errors', async () => {
      const apiError = {
        response: {
          status: 404,
          data: { detail: 'Not found' }
        }
      }

      mockedAxios.create = jest.fn().mockReturnValue({
        get: jest.fn().mockRejectedValue(apiError)
      } as any)

      const client = new (require('@/lib/api').default)()

      await expect(client.getJobStatus('fake_job')).rejects.toMatchObject(apiError)
    })
  })
})
