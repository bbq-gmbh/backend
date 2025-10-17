# Docker Image Publishing Guide

This repository automatically builds and publishes Docker images to GitHub Container Registry (GHCR).

## 🐳 Published Images

**Registry**: `ghcr.io/bbq-gmbh/backend`

**Available Tags**:
- `latest` - Latest build from main branch
- `main` - Latest build from main branch (same as latest)
- `v1.0.0` - Semantic version tags (when you create git tags)
- `main-abc1234` - Specific commit SHA builds

## 📦 How It Works

### Automatic Publishing

The workflow (`.github/workflows/docker.yml`) automatically:

1. **On push to `main`**:
   - Builds Docker image
   - Pushes to GHCR with `latest` and `main` tags
   - Adds commit SHA tag

2. **On version tags** (e.g., `v1.0.0`):
   - Builds Docker image
   - Pushes with version tags: `1.0.0`, `1.0`, `v1.0.0`

3. **On pull requests**:
   - Builds Docker image (validates Dockerfile)
   - Does NOT push (test only)

### Image Visibility

Images are **public by default** after first push. To make them public:

1. Go to: https://github.com/orgs/bbq-gmbh/packages/container/backend/settings
2. Scroll to "Danger Zone"
3. Click "Change visibility" → "Public"

## 🚀 Using the Images

### Pull from GHCR

```bash
# Pull latest
docker pull ghcr.io/bbq-gmbh/backend:latest

# Pull specific version
docker pull ghcr.io/bbq-gmbh/backend:v1.0.0

# Pull specific commit
docker pull ghcr.io/bbq-gmbh/backend:main-abc1234
```

### Use in Docker Compose

```yaml
services:
  backend:
    image: ghcr.io/bbq-gmbh/backend:latest
    ports:
      - "3001:3001"
    environment:
      DATABASE_URL: postgresql://...
```

### Use in Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  template:
    spec:
      containers:
      - name: backend
        image: ghcr.io/bbq-gmbh/backend:latest
```

## 🏷️ Creating Version Tags

To publish a versioned release:

```bash
# Create and push a version tag
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

This will automatically:
- Trigger the Docker workflow
- Build the image
- Push with tags: `v1.0.0`, `1.0.0`, `1.0`

## 🔧 Manual Trigger

You can manually trigger a build:

1. Go to: https://github.com/bbq-gmbh/backend/actions/workflows/docker.yml
2. Click "Run workflow"
3. Select branch
4. Click "Run workflow"

## 🔐 Authentication

### For CI/CD (GitHub Actions)

No setup needed! Uses `GITHUB_TOKEN` automatically.

### For Local Development

```bash
# Login to GHCR
echo $GITHUB_PAT | docker login ghcr.io -u USERNAME --password-stdin

# Or use GitHub CLI
gh auth token | docker login ghcr.io -u USERNAME --password-stdin
```

**Create a Personal Access Token (PAT)**:
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `read:packages`, `write:packages`
4. Copy token and use for login

## 📊 Build Cache

The workflow uses GitHub Actions cache to speed up builds:
- Cached between builds
- Reuses unchanged layers
- Significantly faster builds

## 🐛 Troubleshooting

### Image not showing up?

1. Check workflow ran successfully: https://github.com/bbq-gmbh/backend/actions
2. Check packages page: https://github.com/orgs/bbq-gmbh/packages
3. Make sure you pushed to `main` branch or created a tag

### Permission denied when pulling?

1. Make sure image is public (see "Image Visibility" above)
2. Or authenticate with `docker login ghcr.io`

### Build failing?

1. Check the Dockerfile builds locally: `docker build -t test .`
2. Check workflow logs for errors
3. Verify all dependencies are in `pyproject.toml`

## 📝 Workflow Configuration

Key features in `.github/workflows/docker.yml`:

- ✅ Builds on main push and tags
- ✅ Uses Docker Buildx for better caching
- ✅ Multi-platform support ready (add if needed)
- ✅ Semantic version tagging
- ✅ Build cache with GitHub Actions
- ✅ Only pushes from main branch (not PRs)

## 🔄 Updating the Workflow

To modify the workflow, edit `.github/workflows/docker.yml`:

```yaml
# Example: Add multi-platform builds
- name: Build and push Docker image
  uses: docker/build-push-action@v5
  with:
    platforms: linux/amd64,linux/arm64
    # ... rest of config
```
