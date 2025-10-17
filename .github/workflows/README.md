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
5. ✅ Runs all 35 tests
6. ✅ Generates coverage report (85% coverage)
7. ✅ Uploads coverage to Codecov (optional, requires `CODECOV_TOKEN` secret)

### Requirements

- **No secrets required** for basic operation
- Tests run completely isolated with in-memory SQLite
- No `.env` file needed
- No external services required

### Adding Codecov (Optional)

To enable coverage tracking:

1. Sign up at https://codecov.io
2. Add your repository
3. Copy the upload token
4. Add as GitHub secret: `Settings → Secrets → Actions → New repository secret`
   - Name: `CODECOV_TOKEN`
   - Value: your token

### Viewing Results

- **Actions Tab**: See all workflow runs and logs
- **Pull Requests**: Status checks show pass/fail
- **Branch Protection**: Can require passing tests before merge

### Local Testing

Test what CI will do:

```bash
# Run exactly what CI runs
uv sync
uv run pytest -v
uv run pytest --cov=app --cov-report=xml --cov-report=term
```

### Troubleshooting

If tests fail in CI but pass locally:

1. Check Python version (CI uses 3.14)
2. Verify all dependencies are in `pyproject.toml`
3. Check if tests depend on local files not in git
4. Review workflow logs in Actions tab
