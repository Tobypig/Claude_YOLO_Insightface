'use client'

import { ErrorBoundary } from './ErrorBoundary'
import { ReactNode } from 'react'

/**
 * Client-side wrapper for ErrorBoundary that can be used in Server Components.
 *
 * This component is marked as 'use client' so it can be imported
 * into Server Components (like layout.tsx) while still providing
 * client-side error boundary functionality.
 */
export function ClientErrorBoundary({ children }: { children: ReactNode }) {
  return (
    <ErrorBoundary
      onError={(error, errorInfo) => {
        // Log errors in production to monitoring service
        console.error('Application error:', error)
        console.error('Error info:', errorInfo)

        // In production, send to error tracking service
        // Example: Sentry, LogRocket, Bugsnag, etc.
        if (process.env.NODE_ENV === 'production') {
          // Send error to monitoring service
          // Example: Sentry.captureException(error)
        }
      }}
    >
      {children}
    </ErrorBoundary>
  )
}
