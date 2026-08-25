import { test, expect } from './fixtures';

test.describe('Signal feed', () => {
  test('lists both fixture signals and filters by source', async ({ page }) => {
    await page.goto('/signals');
    await expect(page.locator('.table-row')).toHaveCount(2);

    await page.locator('.filter-pill', { hasText: 'Reddit' }).click();
    await expect(page.locator('.table-row')).toHaveCount(1);
    await expect(page.getByText(/Switching carriers today/)).toBeVisible();

    await page.locator('.filter-pill', { hasText: 'All sources' }).click();
    await expect(page.locator('.table-row')).toHaveCount(2);
  });

  test('opens the detail drawer with full signal content', async ({ page }) => {
    await page.goto('/signals');
    await page.locator('.table-row').filter({ hasText: 'Switching carriers today' }).click();

    const drawer = page.locator('.drawer');
    await expect(drawer).toBeVisible();
    await expect(drawer.getByText('Hot · 82')).toBeVisible();
    await expect(drawer.getByText('Keywords')).toBeVisible();
    await expect(drawer.getByRole('link', { name: 'View original' })).toBeVisible();

    await drawer.getByLabel('Close').click();
    await expect(drawer).toBeHidden();
  });
});
