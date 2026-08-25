import { test, expect } from './fixtures';

test.describe('Overview', () => {
  test('loads with stats and recent signals, no console errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', (err) => errors.push(String(err)));
    page.on('console', (msg) => {
      if (msg.type() === 'error') errors.push(msg.text());
    });

    await page.goto('/');

    await expect(page.locator('.page-title')).toHaveText('Overview');
    await expect(page.locator('.stat-card')).toHaveCount(4);
    await expect(page.getByText('Recent signals')).toBeVisible();
    await expect(page.locator('.table-row')).toHaveCount(2);
    await expect(page.getByText(/Switching carriers today/)).toBeVisible();

    expect(errors).toEqual([]);
  });
});
