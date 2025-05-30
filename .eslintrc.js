module.exports = {
  env: {
    browser: true,
    es2021: true,
    node: true, // For Playwright test files and other Node.js scripts
    mocha: true, // Or jest: true, if using Jest for Playwright tests (Playwright uses its own test runner but syntax can be similar)
  },
  extends: 'eslint:recommended',
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
  },
  rules: {
    'no-unused-vars': ['warn', { argsIgnorePattern: '^_' }], // Warn on unused vars, ignore if prefixed with _
    'no-console': 'off', // Allow console.log for now, can be changed to 'warn' or 'error' in CI
    // Add any project-specific rules here
  },
  ignorePatterns: [
    'venv/',
    'node_modules/',
    'htmlcov/',
    'playwright-report/',
    'dist/', 
    '.pytest_cache/', 
    '*.egg-info/'
  ],
}; 