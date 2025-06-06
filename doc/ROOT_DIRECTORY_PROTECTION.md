# Root Directory Protection Rules

**CRITICAL: ROOT DIRECTORY IS PROTECTED**

## Absolutely Forbidden in Root Directory

❌ **NEVER** put these file types in the root directory:
- `*.py` files (except those explicitly allowed)
- `*.html` files  
- `*.css` files
- `*.js` files (except `eslint.config.js`)
- `*.md` files (except `README.md`, `CONTRIBUTING.md`)
- Any temporary files
- Any development artifacts

## Allowed Files in Root Directory Only

✅ **Only these files are permitted in root:**
- `README.md` - Project documentation
- `CONTRIBUTING.md` - Contribution guidelines  
- `LICENSE` - License file
- `Makefile` - Build and automation
- `pyproject.toml` - Python project config
- `requirements.txt` - Python dependencies
- `package.json` - Node.js dependencies
- `package-lock.json` - Node.js lock file
- `eslint.config.js` - ESLint configuration
- `.gitignore` - Git ignore rules
- `pytest.ini` - Pytest configuration
- `Taskfile.yml` - Task runner config
- Configuration dotfiles (`.eslintrc.js`, etc.)

## Where Files Should Go

📁 **Correct locations for different file types:**

| File Type | Correct Location |
|-----------|------------------|
| Python API code | `src/api/` |
| Python models | `src/models/` |
| Python services | `src/services/` |
| Tests | `tests/` |
| HTML templates | `src/templates/` |
| CSS files | `src/static/css/` |
| JavaScript files | `src/static/js/` |
| Documentation | `doc/` |
| Scripts | `bin/` |
| Configuration | `config/` |

## Enforcement

🛡️ **Multiple layers of protection:**

1. **Git Pre-commit Hook** - Blocks commits with files in root
2. **Makefile Check** - `make lint` includes root directory validation
3. **Manual Review** - All code reviews must check root directory

## If You Violate This Rule

💥 **Consequences:**
- Git pre-commit hook will block your commit
- CI/CD will fail on `make lint`
- Code review will be rejected
- You'll get very frustrated responses about leaving "shit in the root directory"

## Quick Fix Commands

🔧 **If you accidentally add files to root:**

```bash
# Move to correct location
mv inappropriate_file.py src/api/
mv temp_template.html src/templates/
mv styles.css src/static/css/
mv script.js src/static/js/

# Remove if it was just temporary
rm temp_file.html

# Commit the fix
git add -A
git commit -m "fix: move files from root to appropriate directories"
```

**Remember: Keep the root directory clean and organized!**
