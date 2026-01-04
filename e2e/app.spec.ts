import { test, expect } from '@playwright/test';

test.describe('Application End-to-End Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to home page
    await page.goto('http://localhost:3000');
  });

  test('home page loads correctly', async ({ page }) => {
    await expect(page).toHaveTitle(/AI Video Generation/);
    await expect(page.locator('h1')).toContainText('AI Video Generation');
    await expect(page.getByText('Start Generating')).toBeVisible();
    await expect(page.getByText('View Jobs')).toBeVisible();
  });

  test('navigate to create job page', async ({ page }) => {
    await page.click('text=Start Generating');
    await expect(page).toHaveURL('/create');
    await expect(page.getByText('Create Video Generation Job')).toBeVisible();
  });

  test('create a new job', async ({ page }) => {
    // Navigate to create page
    await page.click('text=Start Generating');
    
    // Fill in the form
    await page.fill('input[name="userId"]', 'e2e-test-user');
    await page.fill('textarea[name="prompt"]', 'E2E test video generation');
    
    // Submit the form
    await page.click('text=Generate Video');
    
    // Should redirect to jobs page
    await expect(page).toHaveURL('/jobs');
    await expect(page.getByText('Video Generation Jobs')).toBeVisible();
  });

  test('navigate to jobs page', async ({ page }) => {
    await page.click('text=View Jobs');
    await expect(page).toHaveURL('/jobs');
    await expect(page.getByText('Video Generation Jobs')).toBeVisible();
  });

  test('view jobs list', async ({ page }) => {
    await page.goto('http://localhost:3000/jobs');
    
    // Should show jobs page header
    await expect(page.getByText('Video Generation Jobs')).toBeVisible();
    await expect(page.getByText('View and manage your video generation requests')).toBeVisible();
    
    // Should have control buttons
    await expect(page.getByText('Refresh')).toBeVisible();
    await expect(page.getByText('New Job')).toBeVisible();
  });

  test('navigate to providers page', async ({ page }) => {
    await page.click('text=View health');
    await expect(page).toHaveURL('/providers');
    await expect(page.getByText('AI Providers')).toBeVisible();
  });

  test('view provider health', async ({ page }) => {
    await page.goto('http://localhost:3000/providers');
    
    await expect(page.getByText('AI Providers')).toBeVisible();
    await expect(page.getByText('Monitor health and performance')).toBeVisible();
    await expect(page.getByText('Refresh Status')).toBeVisible();
  });

  test('form validation - empty prompt', async ({ page }) => {
    await page.goto('http://localhost:3000/create');
    
    // Fill only user ID
    await page.fill('input[name="userId"]', 'test-user');
    
    // Try to submit
    await page.click('text=Generate Video');
    
    // Should not submit (button should be disabled or show validation)
    // The button should stay on the page (no redirect)
    await expect(page).toHaveURL('/create');
  });

  test('cancel button returns to previous page', async ({ page }) => {
    await page.goto('http://localhost:3000/create');
    
    await page.click('text=Cancel');
    await expect(page).toHaveURL('/');
  });

  test('responsive design - mobile view', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('http://localhost:3000');
    
    await expect(page.getByText('AI Video Generation')).toBeVisible();
    await expect(page.getByText('Start Generating')).toBeVisible();
  });

  test('api health check', async ({ request }) => {
    const response = await request.get('http://localhost:8000/health');
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data).toHaveProperty('status', 'alive');
  });

  test('create job via API and verify in UI', async ({ page, request }) => {
    // Create a job via API
    const createResponse = await request.post('http://localhost:8000/api/v1/jobs', {
      data: {
        userId: 'e2e-api-test',
        prompt: 'API created job',
        maxRetries: 3,
      },
    });
    
    expect(createResponse.status()).toBe(201);
    const createdJob = await createResponse.json();
    expect(createdJob).toHaveProperty('id');
    
    // Navigate to jobs page
    await page.goto('http://localhost:3000/jobs');
    
    // Job should appear in the list
    await page.waitForTimeout(1000); // Wait for data to load
    await page.click('text=Refresh');
    await page.waitForTimeout(1000);
    
    // Verify the job is displayed (we check for the prompt)
    await expect(page.getByText('API created job')).toBeVisible();
  });

  test('provider status API endpoint', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/providers/status');
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(Array.isArray(data)).toBe(true);
  });

  test('jobs API endpoint', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/jobs');
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data).toHaveProperty('jobs');
    expect(data).toHaveProperty('total');
    expect(Array.isArray(data.jobs)).toBe(true);
  });
});

test.describe('User Flows', () => {
  test('complete user journey: create job and monitor', async ({ page, request }) => {
    // Step 1: Navigate to home
    await page.goto('http://localhost:3000');
    
    // Step 2: Navigate to create page
    await page.click('text=Start Generating');
    await expect(page).toHaveURL('/create');
    
    // Step 3: Create a job
    const userId = `user-${Date.now()}`;
    const prompt = `Test video ${Date.now()}`;
    
    await page.fill('input[name="userId"]', userId);
    await page.fill('textarea[name="prompt"]', prompt);
    await page.click('text=Generate Video');
    
    // Step 4: Verify redirect to jobs page
    await expect(page).toHaveURL('/jobs');
    
    // Step 5: Verify job appears
    await page.waitForTimeout(1000);
    await page.click('text=Refresh');
    await page.waitForTimeout(1000);
    
    // Should see the job (check for prompt text)
    const jobElements = await page.locator('text=' + prompt).all();
    expect(jobElements.length).toBeGreaterThan(0);
    
    // Step 6: Navigate back to home
    await page.click('text=AI Video Generation Platform');
    await expect(page).toHaveURL('/');
  });
});
