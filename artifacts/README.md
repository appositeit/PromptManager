# Artifacts Directory

This directory contains all transient build artifacts, reports, logs, and temporary files generated during development and testing.

## Structure

```
artifacts/
├── coverage/          # Test coverage reports (HTML, XML, etc.)
├── logs/             # Application and server logs
├── reports/          # Lint reports, test reports, code analysis
└── temp/             # Temporary files and build artifacts
```

## Purpose

- **Centralized location** for all generated/transient files
- **Easy cleanup** with `rm -rf artifacts/` or `make clean`
- **Git ignored** - none of these files should be committed
- **Organized** - each type of artifact has its own subdirectory

## Usage

### Coverage Reports
- `make test-cov-html` → `artifacts/coverage/basic/`
- `make test-cov-comprehensive` → `artifacts/coverage/comprehensive/`
- `make test-cov-true` → `artifacts/coverage/true/`

### Logs
- Server logs → `artifacts/logs/`
- Test logs → `artifacts/logs/test/`

### Reports
- ESLint reports → `artifacts/reports/eslint/`
- Code duplication reports → `artifacts/reports/jscpd/`
- Test reports → `artifacts/reports/pytest/`

### Temporary Files
- Build intermediates → `artifacts/temp/`
- Temporary test files → `artifacts/temp/test/`

## Cleanup

All artifacts can be cleaned with:
```bash
make clean              # Remove all artifacts
rm -rf artifacts/       # Manual cleanup
```

**Note:** This entire directory is ignored by Git and should never be committed.
