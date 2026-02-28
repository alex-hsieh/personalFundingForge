import { test, expect } from '@playwright/test';

test.describe('API Integration Tests', () => {
  test('should fetch grants from API', async ({ page }) => {
    // Intercept API call
    const grantsPromise = page.waitForResponse(response => 
      response.url().includes('/api/grants') && response.status() === 200
    );

    await page.goto('/');
    
    // Navigate to discovery to trigger grants fetch
    await page.getByLabel('Role').click();
    await page.getByRole('option', { name: 'Faculty' }).click();
    await page.getByLabel('Year/Level').click();
    await page.getByRole('option', { name: 'Year 1' }).click();
    await page.getByLabel('Program/Department').fill('CS');
    await page.getByRole('button', { name: /forge/i }).click();

    const grantsResponse = await grantsPromise;
    const grants = await grantsResponse.json();

    expect(Array.isArray(grants)).toBe(true);
    expect(grants.length).toBeGreaterThan(0);
    
    // Verify grant structure
    expect(grants[0]).toHaveProperty('id');
    expect(grants[0]).toHaveProperty('name');
    expect(grants[0]).toHaveProperty('targetAudience');
    expect(grants[0]).toHaveProperty('eligibility');
    expect(grants[0]).toHaveProperty('matchCriteria');
  });

  test('should fetch faculty from API', async ({ page }) => {
    const facultyPromise = page.waitForResponse(response => 
      response.url().includes('/api/faculty') && response.status() === 200
    );

    await page.goto('/');
    
    // Navigate through to trigger faculty fetch
    await page.getByLabel('Role').click();
    await page.getByRole('option', { name: 'Faculty' }).click();
    await page.getByLabel('Year/Level').click();
    await page.getByRole('option', { name: 'Year 1' }).click();
    await page.getByLabel('Program/Department').fill('CS');
    await page.getByRole('button', { name: /forge/i }).click();

    // Wait for grants to load and select one
    await page.waitForTimeout(2000);
    const grantCard = page.locator('.grant-card, [data-testid="grant-card"]').first();
    await grantCard.click();

    const facultyResponse = await facultyPromise;
    const faculty = await facultyResponse.json();

    expect(Array.isArray(faculty)).toBe(true);
    
    if (faculty.length > 0) {
      expect(faculty[0]).toHaveProperty('id');
      expect(faculty[0]).toHaveProperty('name');
      expect(faculty[0]).toHaveProperty('department');
      expect(faculty[0]).toHaveProperty('expertise');
    }
  });

  test('should stream forge events via SSE', async ({ page }) => {
    await page.goto('/');
    
    // Complete intake
    await page.getByLabel('Role').click();
    await page.getByRole('option', { name: 'Faculty' }).click();
    await page.getByLabel('Year/Level').click();
    await page.getByRole('option', { name: 'Year 1' }).click();
    await page.getByLabel('Program/Department').fill('CS');
    await page.getByRole('button', { name: /forge/i }).click();

    // Wait for discovery and select grant
    await page.waitForTimeout(2000);
    const grantCard = page.locator('.grant-card, [data-testid="grant-card"]').first();
    await grantCard.click();

    // Monitor network for SSE connection
    const forgeRequest = page.waitForRequest(request => 
      request.url().includes('/api/forge/')
    );

    await forgeRequest;

    // Verify SSE events are being received
    await expect(
      page.getByText(/agent/i).or(page.getByText(/complete/i))
    ).toBeVisible({ timeout: 30000 });
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Mock API failure
    await page.route('**/api/grants', route => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ message: 'Internal Server Error' })
      });
    });

    await page.goto('/');
    
    // Navigate to discovery
    await page.getByLabel('Role').click();
    await page.getByRole('option', { name: 'Faculty' }).click();
    await page.getByLabel('Year/Level').click();
    await page.getByRole('option', { name: 'Year 1' }).click();
    await page.getByLabel('Program/Department').fill('CS');
    await page.getByRole('button', { name: /forge/i }).click();

    // Should show error message
    await expect(
      page.getByText(/couldn't load/i).or(page.getByText(/error/i))
    ).toBeVisible({ timeout: 10000 });
  });

  test('should retry failed API requests', async ({ page }) => {
    let requestCount = 0;

    await page.route('**/api/grants', route => {
      requestCount++;
      if (requestCount === 1) {
        // Fail first request
        route.fulfill({
          status: 500,
          body: JSON.stringify({ message: 'Server Error' })
        });
      } else {
        // Succeed on retry
        route.continue();
      }
    });

    await page.goto('/');
    
    // Navigate to discovery
    await page.getByLabel('Role').click();
    await page.getByRole('option', { name: 'Faculty' }).click();
    await page.getByLabel('Year/Level').click();
    await page.getByRole('option', { name: 'Year 1' }).click();
    await page.getByLabel('Program/Department').fill('CS');
    await page.getByRole('button', { name: /forge/i }).click();

    // Wait for error
    await expect(page.getByText(/couldn't load/i)).toBeVisible({ timeout: 10000 });

    // Click retry
    await page.getByRole('button', { name: /try again/i }).click();

    // Should succeed on second attempt
    await expect(page.getByText('NSF GRFP').or(page.getByText('FSU IDEA Grant'))).toBeVisible({ timeout: 10000 });
  });
});
