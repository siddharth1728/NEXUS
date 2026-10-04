import { test, expect } from '@playwright/test';

test.describe('NEXUS UI End-to-End Tests', () => {
  test('Application should load and render the main layout', async ({ page }) => {
    // Navigate to root
    const response = await page.goto('/');
    
    // We expect the app to load successfully (status 200 or client-side navigation)
    expect(response?.ok()).toBeTruthy();
    
    // Wait for Next.js to render any content
    await page.waitForLoadState('networkidle');
    
    // The page should have some textual content
    const textContent = await page.textContent('body');
    expect(textContent?.length).toBeGreaterThan(0);
  });
});
