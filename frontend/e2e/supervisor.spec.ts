import { test, expect } from '@playwright/test';

test('supervisor dashboard loads and shows basic UI', async ({ page }) => {
  // Login as supervisor first
  await page.goto('/login');
  await page.getByLabel('Username').fill('supervisor1');
  await page.getByLabel('Password').fill('supervisor1-pass');
  await page.getByRole('button', { name: 'Sign in' }).click();

  // Wait for redirect to supervisor dashboard
  await page.waitForURL('/supervisor');

  // Check that basic elements are present
  await expect(page.getByText('Live Session Grid')).toBeVisible();
  await expect(page.getByText('Agent Scorecard Table')).toBeVisible();
});