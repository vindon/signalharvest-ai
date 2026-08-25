import { test, expect } from './fixtures';

test.describe('Brands', () => {
  test('lists the fixture brand', async ({ page }) => {
    await page.goto('/brands');
    await expect(page.getByText('Acme Mobile')).toBeVisible();
    await expect(page.getByText('leads@acme.test · daily')).toBeVisible();
  });

  test('creating a brand shows it in the list', async ({ page }) => {
    await page.goto('/brands');
    await page.getByRole('button', { name: 'New brand' }).click();

    await page.getByLabel('Brand name').fill('Globex Broadband');
    await page.getByLabel('Contact email').fill('leads@globex.test');
    await page.getByRole('button', { name: 'Telecom · Broadband', exact: true }).click();

    await page.getByRole('button', { name: 'Create brand' }).click();

    await expect(page.getByText('Globex Broadband')).toBeVisible();
  });

  test('pausing a brand toggles its status badge', async ({ page }) => {
    await page.goto('/brands');
    const card = page.locator('.panel').filter({ hasText: 'Acme Mobile' });
    await expect(card.getByText('Active')).toBeVisible();

    await card.getByRole('button', { name: 'Pause' }).click();
    await expect(card.getByText('Paused')).toBeVisible();
  });
});
