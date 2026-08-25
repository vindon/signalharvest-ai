import { test, expect } from './fixtures';

test.describe('Run pipeline', () => {
  test('shows run history with the pipeline trail for a completed run', async ({ page }) => {
    await page.goto('/run');
    await expect(page.getByRole('button', { name: 'Run pipeline' })).toBeEnabled();
    await expect(page.getByText('completed', { exact: true })).toBeVisible();
    await expect(page.locator('.pipeline-step-title', { hasText: 'Harvest' })).toBeVisible();
    await expect(page.locator('.pipeline-step-title', { hasText: 'Publish' })).toBeVisible();
    await expect(page.getByText('leads curated')).toBeVisible();
  });

  test('triggering a run adds it to run history', async ({ page }) => {
    await page.goto('/run');
    await expect(page.locator('.panel')).toHaveCount(1); // 1 run card
    await page.getByRole('button', { name: 'Run pipeline' }).click();
    await expect(page.locator('.panel')).toHaveCount(2); // 2 run cards
  });
});
