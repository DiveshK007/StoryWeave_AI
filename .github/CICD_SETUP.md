# CI/CD Pipeline Setup Guide

This document provides an overview of the CI/CD pipeline setup for StoryWeave AI.

## Overview

The CI/CD pipeline consists of the following workflows:

1. **CI** (`ci.yml`) - Continuous Integration on every push and PR
2. **Deploy** (`deploy.yml`) - Deployment to staging and production
3. **Dependency Update** (`dependency-update.yml`) - Tests dependency updates from Dependabot
4. **Security Scan** (`security-scan.yml`) - Security vulnerability scanning

## CI Workflow

The CI workflow runs on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

### Jobs

1. **Python Lint** - Runs `ruff` and `black` to check code style
2. **Python Type Check** - Runs `mypy` for type checking
3. **Python Tests** - Runs `pytest` with coverage (minimum 70% required)
4. **Frontend Lint** - Runs `ESLint` for JavaScript/TypeScript linting
5. **Frontend Type Check** - Runs `tsc` for TypeScript type checking
6. **Frontend Build** - Builds the Vite frontend application

## Deployment Workflow

The deployment workflow triggers after CI passes successfully.

### Environments

- **Staging**: Deploys from `develop` branch
- **Production**: Deploys from `main` branch

### Deployment Steps

1. Backend deployment to Render/Railway
2. Database migrations (Alembic)
3. Frontend deployment to Vercel/Netlify
4. Slack notification

## Security Scanning

Security scanning runs:
- On every push and PR
- Weekly on Mondays at 9 AM UTC (scheduled)

### Tools Used

- **Safety** - Python dependency vulnerability scanner
- **Bandit** - Python security linter
- **npm audit** - Node.js dependency vulnerability scanner
- **Snyk** - Advanced security scanning (optional, requires token)
- **CodeQL** - GitHub's code analysis tool

## Dependabot Configuration

Dependabot is configured to automatically create PRs for:
- Python dependencies (weekly on Monday)
- Node.js dependencies (weekly on Monday)
- GitHub Actions (weekly on Monday)

## Setup Steps

1. **Configure GitHub Secrets**
   - See [SECRETS_SETUP.md](./SECRETS_SETUP.md) for detailed instructions

2. **Update README Badges**
   - Replace `YOUR_USERNAME` in `README.md` with your GitHub username

3. **Set up Environments** (Optional but recommended)
   - Go to Settings > Environments
   - Create `staging` and `production` environments
   - Add environment-specific secrets

4. **Enable GitHub Actions**
   - Go to Settings > Actions > General
   - Ensure "Allow all actions and reusable workflows" is enabled

5. **Configure Codecov** (Optional)
   - Sign up at https://codecov.io
   - Connect your repository
   - Add `CODECOV_TOKEN` secret if using private repos

6. **Test the Pipeline**
   - Push a commit to `develop` branch to test CI
   - Verify all checks pass
   - Check that deployment triggers correctly

## Customization

### Changing Coverage Threshold

Edit `.coveragerc` or `pytest.ini`:
```ini
fail_under = 80  # Change from 70 to 80
```

### Changing Deployment Platform

Edit `.github/workflows/deploy.yml`:
- Replace Render API calls with Railway API
- Update Vercel deployment with Netlify deployment
- Adjust environment variables as needed

### Adding More Tests

Add test files to:
- `agentic-aws-nvidia-demo/services/orchestrator/tests/` for Python
- `frontend/src/**/*.test.ts` or `frontend/src/**/*.test.tsx` for TypeScript

## Troubleshooting

### CI Fails on Coverage

If coverage is below 70%:
1. Write more tests for uncovered code
2. Temporarily lower threshold in `pytest.ini`
3. Add `# pragma: no cover` comments for intentionally untested code

### Deployment Fails

1. Check GitHub Actions logs for specific errors
2. Verify all required secrets are set
3. Ensure API keys have correct permissions
4. Check deployment platform status

### Type Checking Fails

1. Fix TypeScript type errors
2. Add type annotations where needed
3. Update `tsconfig.json` if needed

## Monitoring

- View workflow runs: Repository > Actions tab
- Check deployment status: Badges in README
- Monitor coverage: Codecov dashboard (if configured)

## Next Steps

- [ ] Configure all required secrets
- [ ] Update README badges with your username
- [ ] Set up environments for staging/production
- [ ] Test the pipeline with a test commit
- [ ] Configure Codecov (optional)
- [ ] Set up Slack notifications (optional)
