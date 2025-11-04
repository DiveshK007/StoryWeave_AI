# GitHub Secrets Setup Guide

This document outlines all the secrets that need to be configured in your GitHub repository settings for the CI/CD pipeline to work correctly.

## Accessing GitHub Secrets

1. Go to your repository on GitHub
2. Navigate to **Settings** > **Secrets and variables** > **Actions**
3. Click **New repository secret** to add each secret

## Required Secrets

### Deployment Secrets

#### Render (Backend Deployment)
- **`RENDER_API_KEY`** - Production Render API key
  - Get it from: Render Dashboard > Account Settings > API Keys
- **`RENDER_SERVICE_ID`** - Production Render service ID
  - Find it in your Render service URL or dashboard
- **`RENDER_STAGING_API_KEY`** - Staging Render API key (if using separate account)
- **`RENDER_STAGING_SERVICE_ID`** - Staging Render service ID

#### Railway (Alternative Backend Deployment)
- **`RAILWAY_TOKEN`** - Railway API token
  - Get it from: Railway Dashboard > Account Settings > API Tokens

#### Vercel (Frontend Deployment)
- **`VERCEL_TOKEN`** - Vercel API token
  - Get it from: Vercel Dashboard > Settings > Tokens
- **`VERCEL_ORG_ID`** - Vercel organization ID
- **`VERCEL_PROJECT_ID`** - Production Vercel project ID
- **`VERCEL_STAGING_PROJECT_ID`** - Staging Vercel project ID (optional)
- **`VERCEL_STAGING_DOMAIN`** - Staging domain (optional)

#### Netlify (Alternative Frontend Deployment)
- **`NETLIFY_AUTH_TOKEN`** - Netlify API token
  - Get it from: Netlify Dashboard > User Settings > Applications > New access token
- **`NETLIFY_SITE_ID`** - Production Netlify site ID
- **`NETLIFY_STAGING_SITE_ID`** - Staging Netlify site ID

### Database Secrets

- **`DATABASE_URL`** - Production database connection string
  - Format: `postgresql://user:password@host:port/database`
- **`STAGING_DATABASE_URL`** - Staging database connection string

### Application Secrets

- **`NIM_API_KEY`** - NVIDIA NIM API key (if using NVIDIA services)
  - Get it from: NVIDIA NGC dashboard

### Notification Secrets

- **`SLACK_WEBHOOK_URL`** - Slack webhook URL for deployment notifications
  - Create a webhook: Slack App > Incoming Webhooks > Add New Webhook

### Security Scanning (Optional)

- **`SNYK_TOKEN`** - Snyk API token for advanced security scanning
  - Get it from: Snyk Dashboard > Account Settings > API Token

## Environment-Specific Secrets

GitHub Actions supports **environments** for managing secrets per deployment stage:

1. Go to **Settings** > **Environments**
2. Create two environments: `staging` and `production`
3. Add environment-specific secrets to each

### Staging Environment
- `STAGING_DATABASE_URL`
- `RENDER_STAGING_API_KEY`
- `RENDER_STAGING_SERVICE_ID`
- `VERCEL_STAGING_PROJECT_ID`

### Production Environment
- `DATABASE_URL`
- `RENDER_API_KEY`
- `RENDER_SERVICE_ID`
- `VERCEL_PROJECT_ID`

## Verification

After setting up secrets, you can verify they're working by:

1. Pushing a commit to the `main` or `develop` branch
2. Checking the Actions tab to see if workflows run successfully
3. Reviewing workflow logs (secrets are masked in logs for security)

## Security Best Practices

- ✅ Never commit secrets to the repository
- ✅ Use environment-specific secrets for staging/production
- ✅ Rotate secrets regularly
- ✅ Use the minimum required permissions for API tokens
- ✅ Review and limit access to secrets (use environments with required reviewers for production)

## Troubleshooting

### "Secret not found" error
- Verify the secret name matches exactly (case-sensitive)
- Ensure the secret is set at the repository level (not organization level if not needed)

### Deployment fails
- Check that API keys have the correct permissions
- Verify service IDs are correct
- Ensure database URLs are accessible from the deployment platform

### Slack notifications not working
- Verify the webhook URL is correct
- Test the webhook manually with curl
- Check Slack channel permissions
