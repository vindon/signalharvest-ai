import { test as base, expect } from '@playwright/test';

const MOCK_BACKEND_URL = 'http://localhost:8002';

// All fixture state lives in the single shared mock-backend process for the
// whole run, not per-test — reset it before every test, in every spec file,
// so no test's outcome can depend on what an earlier test did to it.
export const test = base.extend<{ resetBackend: void }>({
  resetBackend: [
    async ({ request }, use) => {
      await request.post(`${MOCK_BACKEND_URL}/e2e/reset`);
      await use();
    },
    { auto: true },
  ],
});

export { expect };
