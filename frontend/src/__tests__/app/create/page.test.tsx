import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { useRouter } from 'next/navigation';
import CreateJobPage from '@/app/create/page';
import { api } from '@/lib/api';

// Mock the router
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
}));

// Mock the API
vi.mock('@/lib/api', () => ({
  api: {
    jobs: {
      create: vi.fn(),
    },
  },
}));

describe('CreateJobPage', () => {
  const mockPush = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useRouter as vi.Mock).mockReturnValue({
      push: mockPush,
    });
  });

  it('renders the form correctly', () => {
    render(<CreateJobPage />);

    expect(screen.getByLabelText('User ID')).toBeInTheDocument();
    expect(screen.getByLabelText('Prompt')).toBeInTheDocument();
    expect(screen.getByText('Generate Video')).toBeInTheDocument();
    expect(screen.getByText('Cancel')).toBeInTheDocument();
  });

  it('shows validation error when prompt is empty', async () => {
    render(<CreateJobPage />);

    const submitButton = screen.getByText('Generate Video');
    fireEvent.click(submitButton);

    // Form should not submit
    expect(api.jobs.create).not.toHaveBeenCalled();
  });

  it('creates job successfully and redirects', async () => {
    const mockJob = {
      id: '123',
      userId: 'user1',
      prompt: 'Test prompt',
      status: 'queued',
    };

    (api.jobs.create as vi.Mock).mockResolvedValueOnce(mockJob);

    render(<CreateJobPage />);

    const userIdInput = screen.getByLabelText('User ID');
    const promptInput = screen.getByLabelText('Prompt');
    const submitButton = screen.getByText('Generate Video');

    fireEvent.change(userIdInput, { target: { value: 'user1' } });
    fireEvent.change(promptInput, { target: { value: 'Test prompt' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(api.jobs.create).toHaveBeenCalledWith({
        userId: 'user1',
        prompt: 'Test prompt',
        maxRetries: 3,
      });
    });

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/jobs');
    });
  });

  it('shows error message when API call fails', async () => {
    (api.jobs.create as vi.Mock).mockRejectedValueOnce(
      new Error('API Error')
    );

    render(<CreateJobPage />);

    const userIdInput = screen.getByLabelText('User ID');
    const promptInput = screen.getByLabelText('Prompt');
    const submitButton = screen.getByText('Generate Video');

    fireEvent.change(userIdInput, { target: { value: 'user1' } });
    fireEvent.change(promptInput, { target: { value: 'Test prompt' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('API Error')).toBeInTheDocument();
    });
  });

  it('navigates back when Cancel is clicked', () => {
    render(<CreateJobPage />);

    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);

    // router.back() should be called
    const router = useRouter();
    expect(router.back).toHaveBeenCalled();
  });
});
