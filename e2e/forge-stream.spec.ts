import { test, expect } from '@playwright/test';

test.describe('Forge Stream Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    
    // Complete intake
    await page.getByLabel('Role').click();
    await page.getByRole('option', { name: 'Faculty' }).click();
    await page.getByLabel('Year/Level').click();
    await page.getByRole('option', { name: 'Year 1' }).click();
    await page.getByLabel('Program/Department').fill('Computer Science');
    await page.getByRole('button', { name: /forge/i }).click();

    // Wait for discovery
    await expect(page.getByText('Discovery Dashboard')).toBeVisible();
  });

  test('should stream forge progress events', async ({ page }) => {
    // Select first grant
    const grantCard = page.locator('.grant-card, [data-testid="grant-card"]').first();
    await grantCard.click();

    // Wait for streaming to start
    await expect(page.getByText(/agent/i).or(page.getByText(/step/i))).toBeVisible({ timeout: 10000 });

    // Verify multiple progress events appear
    await page.waitForTimeout(2000);
    
    // Should see agent names or progress indicators
    const progressIndicators = page.locator('text=/sourcing|matchmaking|collaborator|drafting|complete/i');
    await expect(progressIndicators.first()).toBeVisible({ timeout: 30000 });
  });

  test('should display final forge results', async ({ page }) => {
    // Select first grant
    const grantCard = page.locator('.grant-card, [data-testid="grant-card"]').first();
    await grantCard.click();

    // Wait for completion
    await expect(
      page.getByText(/complete/i).or(page.getByText(/done/i))
    ).toBeVisible({ timeout: 60000 });

    // Verify result sections are displayed
    await expect(
      page.getByText(/proposal/i).or(page.getByText(/draft/i))
    ).toBeVisible({ timeout: 5000 });
  });

  test('should handle forge stream with mock fallback', async ({ page }) => {
    // Mock agent service unavailable
    await page.route('**/api/forge/*', async route => {
      // Simulate SSE stream with mock data
      const mockEvents = [
        'data: {"step":"SourcingAgent: Extracting CV data...","done":false}\n\n',
        'data: {"step":"MatchmakingAgent: Analyzing match criteria...","done":false}\n\n',
        'data: {"step":"CollaboratorAgent: Finding relevant faculty...","done":false}\n\n',
        'data: {"step":"DraftingAgent: Generating proposal draft...","done":false}\n\n',
        'data: {"step":"Complete","done":true,"result":{"proposalDraft":"Mock proposal","collaborators":[],"matchScore":75}}\n\n'
      ];

      await route.fulfill({
        status: 200,
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive'
        },
        body: mockEvents.join('')
      });
    });

    // Select first grant
    const grantCard = page.locator('.grant-card, [data-testid="grant-card"]').first();
    await grantCard.click();

    // Verify mock events are displayed
    await expect(page.getByText(/sourcing/i)).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/matchmaking/i)).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/complete/i)).toBeVisible({ timeout: 30000 });
  });

  test('should handle forge stream errors', async ({ page }) => {
    // Mock forge endpoint error
    await page.route('**/api/forge/*', route => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ message: 'Forge service error' })
      });
    });

    // Select first grant
    const grantCard = page.locator('.grant-card, [data-testid="grant-card"]').first();
    await grantCard.click();

    // Should show error state
    await expect(
      page.getByText(/error/i).or(page.getByText(/failed/i))
    ).toBeVisible({ timeout: 10000 });
  });

  test('should display collaborator recommendations', async ({ page }) => {
    // Select first grant
    const grantCard = page.locator('.grant-card, [data-testid="grant-card"]').first();
    await grantCard.click();

    // Wait for forge to complete
    await expect(page.getByText(/complete/i)).toBeVisible({ timeout: 60000 });

    // Verify collaborators section exists
    await expect(
      page.getByText(/collaborator/i).or(page.getByText(/faculty/i))
    ).toBeVisible({ timeout: 5000 });
  });

  test('should display compliance checklist', async ({ page }) => {
    // Select first grant
    const grantCard = page.locator('.grant-card, [data-testid="grant-card"]').first();
    await grantCard.click();

    // Wait for forge to complete
    await expect(page.getByText(/complete/i)).toBeVisible({ timeout: 60000 });

    // Verify compliance section exists
    await expect(
      page.getByText(/compliance/i).or(page.getByText(/checklist/i)).or(page.getByText(/ramp/i))
    ).toBeVisible({ timeout: 5000 });
  });

  test('should display proposal draft', async ({ page }) => {
    // Select first grant
    const grantCard = page.locator('.grant-card, [data-testid="grant-card"]').first();
    await grantCard.click();

    // Wait for forge to complete
    await expect(page.getByText(/complete/i)).toBeVisible({ timeout: 60000 });

    // Verify proposal section exists
    await expect(
      page.getByText(/proposal/i).or(page.getByText(/draft/i))
    ).toBeVisible({ timeout: 5000 });
  });
});
