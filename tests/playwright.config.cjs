// playwright.config.cjs
const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests/e2e', // Directory containing E2E test files
  fullyParallel: true, // Run tests in files in parallel
  forbidOnly: !!process.env.CI, // Fail the build on CI if you accidentally left test.only in the source code
  retries: process.env.CI ? 2 : 0, // Retry on CI only
  workers: process.env.CI ? 1 : undefined, // Opt for fewer workers on CI
  reporter: [['html', { open: 'never' }]], // Reporter to use, prevent auto-opening report
  use: {
    baseURL: 'http://localhost:8081', // Base URL for actions like page.goto('/')
    trace: 'on-first-retry', // Record trace only when retrying a failed test
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    // Optionally, add more browsers
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },
  ],
  // Optionally, configure a web server to start before tests
  // webServer: {
  //   command: 'npm run start', // Command to start your dev server
  //   url: 'http://localhost:8081',
  //   reuseExistingServer: !process.env.CI,
  // },
}); 