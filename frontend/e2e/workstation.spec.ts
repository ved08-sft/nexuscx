import { test, expect } from '@playwright/test';

test('workstation loads and shows basic UI', async ({ page }) => {
  // Login as agent first
  await page.goto('/login');
  await page.getByLabel('Username').fill('agent1');
  await page.getByLabel('Password').fill('agent1-pass');
  await page.getByRole('button', { name: 'Sign in' }).click();

  // Wait for redirect to workstation (using a demo session ID)
  await page.waitForURL('/workstation/**');

  // Check that basic elements are present
  await expect(page.getByText('Live Stream Transcript')).toBeVisible();
  await expect(page.getByText('AI Suggestion')).toBeVisible();
  await expect(page.getByText('SOP Context')).toBeVisible();
  await expect(page.getByText('Compliance Checklist')).toBeVisible();
});