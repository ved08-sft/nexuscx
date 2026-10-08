import { test, expect } from '@playwright/test';

test('WebSocket reconnects after disconnection', async ({ page }) => {
  // Login as agent first
  await page.goto('/login');
  await page.getByLabel('Username').fill('agent1');
  await page.getByLabel('Password').fill('agent1-pass');
  await page.getByRole('button', { name: 'Sign in' }).click();

  // Wait for redirect to workstation (using a demo session ID)
  await page.waitForURL('/workstation/**');

  // Check that we're connected initially
  await expect(page.getByTestId('ws-status')).toHaveAttribute('data-status', 'open');

  // Go offline to simulate disconnection
  await page.context().setOffline(true);
  await expect(page.getByTestId('ws-status')).toHaveAttribute('data-status', 'reconnecting');

  // Go back online
  await page.context().setOffline(false);
  await expect(page.getByTestId('ws-status')).toHaveAttribute('data-status', 'open');
});