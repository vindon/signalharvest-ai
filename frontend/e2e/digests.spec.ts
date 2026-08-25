import { test, expect } from './fixtures';

test.describe('Digests', () => {
  test('lists the fixture digest and opens its detail', async ({ page }) => {
    await page.goto('/digests');
    await expect(page.locator('.table-row')).toHaveCount(1);
    await expect(page.getByText('Acme Mobile')).toBeVisible();
    await expect(page.locator('.table-row').getByText('Delivered', { exact: true })).toBeVisible();

    await page.locator('.table-row').first().click();
    const drawer = page.locator('.drawer');
    await expect(drawer).toBeVisible();
    await expect(drawer.getByText('1 lead', { exact: true })).toBeVisible();
    await expect(drawer.getByRole('link', { name: /Download CSV/ })).toBeVisible();
  });
});
