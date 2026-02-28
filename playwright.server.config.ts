import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './server/__tests__',
  fullyParallel: false, // Run tests sequentially to avoid DB conflicts
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1, // Single worker to avoid DB conflicts
  reporter: 'html',
  use: {
    trace: 'on-first-retry',
  },
  timeout: 30000,
  // No webServer needed for server tests - they start their own test server
});
