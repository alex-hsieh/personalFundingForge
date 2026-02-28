import { test, expect } from '@playwright/test';

test.describe('Full Application Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should complete full grant discovery and forge flow', async ({ page }) => {
    // Stage 1: Intake Form
    await expect(page.getByText('Intake')).toBeVisible();
    await expect(page.getByText('Current stage: Intake')).toBeVisible();

    // Fill out intake form
    await page.getByLabel('Role').click();
    await page.getByRole('option', { name: 'Faculty' }).click();

    await page.getByLabel('Year/Level').click();
    await page.getByRole('option', { name: 'Year 1' }).click();

    await page.getByLabel('Program/Department').fill('Computer Science');

    // Submit intake form
    await page.getByRole('button', { name: /forge/i }).click();

    // Stage 2: Discovery Dashboard
    await expect(page.getByText('Discovery Dashboard')).toBeVisible();
    await expect(page.getByText('Current stage: Discovery')).toBeVisible();

    // Verify profile badges are displayed
    await expect(page.getByText('Role:')).toBeVisible();
    await expect(page.getByText('Faculty')).toBeVisible();

    // Wait for grants to load
    await expect(page.getByText('NSF GRFP').or(page.getByText('FSU IDEA Grant'))).toBeVisible({ timeout: 10000 });

    // Test search functionality
    await page.getByPlaceholder('Search grants, criteria, eligibility…').fill('NSF');
    await expect(page.getByText('NSF GRFP').or(page.getByText('NSF CAREER'))).toBeVisible();

    // Clear search
    await page.getByRole('button', { name: /clear/i }).click();
    await expect(page.getByPlaceholder('Search grants, criteria, eligibility…')).toHaveValue('');

    // Test audience filter
    await page.getByRole('button', { name: 'Faculty', exact: true }).click();
    
    // Select a grant
    const grantCard = page.locator('.grant-card, [data-testid="grant-card"]').first();
    await grantCard.click();

    // Stage 3: Final Packet (Forge)
    await expect(page.getByText('Final Packet').or(page.getByText('Packet'))).toBeVisible();
    
    // Wait for forge stream to start
    await expect(page.getByText(/agent/i).or(page.getByText(/complete/i))).toBeVisible({ timeout: 30000 });

    // Verify forge results appear
    await expect(
      page.getByText(/proposal/i).or(page.getByText(/draft/i)).or(page.getByText(/collaborator/i))
    ).toBeVisible({ timeout: 60000 });
  });

  test('should handle grant search and filtering', async ({ page }) => {
    // Navigate to discovery (skip intake for this test)
    await page.goto('/?stage=discovery&role=Faculty&year=Year+1&program=CS');

    await expect(page.getByText('Discovery Dashboard')).toBeVisible();

    // Test search
    const searchInput = page.getByPlaceholder('Search grants, criteria, eligibility…');
    await searchInput.fill('GRFP');
    
    await expect(page.getByText('NSF GRFP')).toBeVisible();

    // Test that non-matching grants are filtered out
    await searchInput.fill('xyz123nonexistent');
    await expect(page.getByText('No matches found')).toBeVisible();

    // Reset search
    await page.getByRole('button', { name: /reset search/i }).click();
    await expect(searchInput).toHaveValue('');
  });

  test('should display faculty list', async ({ page }) => {
    // Navigate to discovery
    await page.goto('/?stage=discovery&role=Faculty&year=Year+1&program=CS');

    // Select a grant to trigger forge
    const grantCard = page.locator('.grant-card, [data-testid="grant-card"]').first();
    await grantCard.click();

    // Wait for collaborators section
    await expect(
      page.getByText(/collaborator/i).or(page.getByText(/faculty/i))
    ).toBeVisible({ timeout: 60000 });
  });

  test('should handle back navigation', async ({ page }) => {
    // Complete intake
    await page.getByLabel('Role').click();
    await page.getByRole('option', { name: 'Faculty' }).click();
    await page.getByLabel('Year/Level').click();
    await page.getByRole('option', { name: 'Year 1' }).click();
    await page.getByLabel('Program/Department').fill('Computer Science');
    await page.getByRole('button', { name: /forge/i }).click();

    // Wait for discovery
    await expect(page.getByText('Discovery Dashboard')).toBeVisible();

    // Select grant
    const grantCard = page.locator('.grant-card, [data-testid="grant-card"]').first();
    await grantCard.click();

    // Wait for packet stage
    await expect(page.getByText(/packet/i)).toBeVisible();

    // Go back to discovery
    const backButton = page.getByRole('button', { name: /back/i });
    if (await backButton.isVisible()) {
      await backButton.click();
      await expect(page.getByText('Discovery Dashboard')).toBeVisible();
    }
  });

  test('should handle errors gracefully', async ({ page }) => {
    // Test with invalid grant ID
    await page.goto('/?stage=packet&grantId=999999');

    // Should show error or redirect to intake
    await expect(
      page.getByText(/error/i).or(page.getByText('Intake'))
    ).toBeVisible({ timeout: 5000 });
  });
});
