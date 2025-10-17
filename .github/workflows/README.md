# GitHub Actions Workflows

## Tests Workflow

**File**: `.github/workflows/test.yml`

### Triggers

1. **Automatic on Push to Main**
   - Runs when code is pushed to the `main` branch
   - Ensures main branch always has passing tests

2. **Automatic on Pull Requests**
   - Runs on all PRs targeting `main` branch
   - Prevents merging broken code

3. **Manual Trigger** (workflow_dispatch)
   - Go to: **Actions** tab → **Tests** workflow → **Run workflow** button
   - Select the branch you want to test
   - Click "Run workflow"

### What It Does

1. ✅ Checks out code (`actions/checkout@v5`)
2. ✅ Installs uv (`astral-sh/setup-uv@v6`) with caching enabled
3. ✅ Sets up Python (respects `requires-python` in pyproject.toml)
4. ✅ Installs dependencies with `uv sync --all-groups`
5. ✅ Runs all 35 tests with coverage report (85% coverage)
6. ✅ Shows coverage in terminal output (no external services needed)

### Requirements

- **No secrets required**
- **No external services** - Everything runs in GitHub Actions
- Tests run completely isolated with in-memory SQLite
- No `.env` file needed
- Coverage reports shown directly in CI logs

### Viewing Results

- **Actions Tab**: See all workflow runs and logs
- **Pull Requests**: Status checks show pass/fail
- **Branch Protection**: Can require passing tests before merge

### Local Testing

Test what CI will do:

```bash
# Run exactly what CI runs
uv sync --all-groups
uv run pytest -v --cov=app --cov-report=term-missing
```

### Troubleshooting

If tests fail in CI but pass locally:

1. Check Python version (CI uses 3.14)
2. Verify all dependencies are in `pyproject.toml`
3. Check if tests depend on local files not in git
4. Review workflow logs in Actions tab
