import { render, screen, waitFor } from '@testing-library/react';
import JobsPage from '@/app/jobs/page';
import { api } from '@/lib/api';
import { Job } from '@/types';

// Mock API
vi.mock('@/lib/api', () => ({
  api: {
    jobs: {
      list: vi.fn(),
    },
  },
}));

describe('JobsPage', () => {
  const mockJobs: Job[] = [
    {
      id: '1',
      userId: 'user1',
      status: 'queued',
      prompt: 'Test prompt 1',
      retryCount: 0,
      maxRetries: 3,
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-01T00:00:00Z',
    },
    {
      id: '2',
      userId: 'user1',
      status: 'completed',
      prompt: 'Test prompt 2',
      retryCount: 0,
      maxRetries: 3,
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-01T00:00:00Z',
      completedAt: '2024-01-01T00:05:00Z',
      result: {
        videoUrl: 'http://example.com/video.mp4',
      },
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders jobs list on load', async () => {
    (api.jobs.list as vi.Mock).mockResolvedValueOnce(mockJobs);

    render(<JobsPage />);

    await waitFor(() => {
      expect(screen.getByText('Video Generation Jobs')).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(api.jobs.list).toHaveBeenCalled();
    });
  });

  it('shows loading state initially', () => {
    (api.jobs.list as vi.Mock).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<JobsPage />);

    expect(screen.getByText('Video Generation Jobs')).toBeInTheDocument();
  });

  it('displays error message when API fails', async () => {
    (api.jobs.list as vi.Mock).mockRejectedValueOnce(
      new Error('Failed to fetch')
    );

    render(<JobsPage />);

    await waitFor(() => {
      expect(screen.getByText('Failed to fetch')).toBeInTheDocument();
    });
  });

  it('shows empty state when no jobs exist', async () => {
    (api.jobs.list as vi.Mock).mockResolvedValueOnce([]);

    render(<JobsPage />);

    await waitFor(() => {
      expect(
        screen.getByText('No jobs found. Start by creating a new one!')
      ).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText('Create your first job')).toBeInTheDocument();
    });
  });

  it('refreshes jobs when refresh button is clicked', async () => {
    (api.jobs.list as vi.Mock).mockResolvedValueOnce(mockJobs);

    render(<JobsPage />);

    await waitFor(() => {
      expect(api.jobs.list).toHaveBeenCalledTimes(1);
    });

    const refreshButton = screen.getByText('Refresh');
    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(api.jobs.list).toHaveBeenCalledTimes(2);
    });
  });

  it('navigates to create page when New Job button is clicked', async () => {
    (api.jobs.list as vi.Mock).mockResolvedValueOnce([]);

    render(<JobsPage />);

    await waitFor(() => {
      const newJobButton = screen.getByText('New Job');
      expect(newJobButton.closest('a')).toHaveAttribute('href', '/create');
    });
  });
});
