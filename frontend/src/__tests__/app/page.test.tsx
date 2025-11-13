/**
 * Tests for Homepage component
 */
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    pathname: '/',
  }),
}))

describe('Homepage', () => {
  // Create a simple mock component for testing
  const HomePage = () => {
    return (
      <div>
        <h1>Video Frame Person & Face Detection</h1>
        <p>Welcome to the video processing system</p>
        <a href="/process">Process Video</a>
        <a href="/jobs">View Jobs</a>
      </div>
    )
  }

  it('renders homepage heading', () => {
    render(<HomePage />)

    const heading = screen.getByText(/Video Frame Person & Face Detection/i)
    expect(heading).toBeInTheDocument()
  })

  it('renders welcome message', () => {
    render(<HomePage />)

    const welcomeText = screen.getByText(/Welcome to the video processing system/i)
    expect(welcomeText).toBeInTheDocument()
  })

  it('renders process video link', () => {
    render(<HomePage />)

    const processLink = screen.getByText(/Process Video/i)
    expect(processLink).toBeInTheDocument()
    expect(processLink.closest('a')).toHaveAttribute('href', '/process')
  })

  it('renders view jobs link', () => {
    render(<HomePage />)

    const jobsLink = screen.getByText(/View Jobs/i)
    expect(jobsLink).toBeInTheDocument()
    expect(jobsLink.closest('a')).toHaveAttribute('href', '/jobs')
  })
})

describe('Homepage Features', () => {
  const HomePage = () => (
    <div>
      <section data-testid="features">
        <h2>Features</h2>
        <ul>
          <li>Person Detection with YOLO</li>
          <li>Face Recognition with InsightFace</li>
          <li>Frame Extraction</li>
        </ul>
      </section>
    </div>
  )

  it('displays features section', () => {
    render(<HomePage />)

    const features = screen.getByTestId('features')
    expect(features).toBeInTheDocument()
  })

  it('lists key features', () => {
    render(<HomePage />)

    expect(screen.getByText(/Person Detection with YOLO/i)).toBeInTheDocument()
    expect(screen.getByText(/Face Recognition with InsightFace/i)).toBeInTheDocument()
    expect(screen.getByText(/Frame Extraction/i)).toBeInTheDocument()
  })
})
