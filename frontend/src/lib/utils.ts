/**
 * Utility functions
 */

/**
 * Format bytes to human-readable size
 */
export function formatBytes(bytes: number, decimals: number = 2): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/**
 * Format timestamp (seconds) to HH:MM:SS
 */
export function formatTimestamp(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  const ms = Math.floor((seconds % 1) * 1000);

  const hh = hours.toString().padStart(2, '0');
  const mm = minutes.toString().padStart(2, '0');
  const ss = secs.toString().padStart(2, '0');
  const mmm = ms.toString().padStart(3, '0');

  return `${hh}:${mm}:${ss}.${mmm}`;
}

/**
 * Parse timestamp string to seconds
 */
export function parseTimestamp(timestamp: string): number {
  try {
    // Try parsing as float (seconds)
    const seconds = parseFloat(timestamp);
    if (!isNaN(seconds)) {
      return seconds;
    }

    // Parse as time format
    const parts = timestamp.split(':');
    if (parts.length === 3) {
      // HH:MM:SS.mmm
      const [h, m, s] = parts;
      return parseInt(h) * 3600 + parseInt(m) * 60 + parseFloat(s);
    } else if (parts.length === 2) {
      // MM:SS.mmm
      const [m, s] = parts;
      return parseInt(m) * 60 + parseFloat(s);
    }

    return 0;
  } catch {
    return 0;
  }
}

/**
 * Debounce function
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;

  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      timeout = null;
      func(...args);
    };

    if (timeout) {
      clearTimeout(timeout);
    }
    timeout = setTimeout(later, wait);
  };
}

/**
 * Throttle function
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;

  return function executedFunction(...args: Parameters<T>) {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

/**
 * Class name helper (simple version of clsx)
 */
export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
}

/**
 * Download file from blob
 */
export function downloadBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

/**
 * Format similarity score as percentage
 */
export function formatSimilarity(similarity: number): string {
  return `${(similarity * 100).toFixed(1)}%`;
}

/**
 * Get similarity color
 */
export function getSimilarityColor(similarity: number): string {
  if (similarity >= 0.8) return 'text-green-600';
  if (similarity >= 0.6) return 'text-yellow-600';
  return 'text-red-600';
}

/**
 * Validate video file
 */
export function isValidVideoFile(file: File): boolean {
  const allowedFormats = ['mp4', 'mov', 'avi', 'mkv'];
  const ext = file.name.split('.').pop()?.toLowerCase();
  return ext ? allowedFormats.includes(ext) : false;
}

/**
 * Validate image file
 */
export function isValidImageFile(file: File): boolean {
  const allowedFormats = ['jpg', 'jpeg', 'png', 'webp'];
  const ext = file.name.split('.').pop()?.toLowerCase();
  return ext ? allowedFormats.includes(ext) : false;
}
