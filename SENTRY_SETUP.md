# Sentry Integration Guide

This guide covers the complete Sentry integration for StoryWeave AI, including backend and frontend setup, configuration, and usage examples.

## Overview

Sentry provides error tracking, performance monitoring, and user feedback for both the FastAPI backend and React frontend. This integration includes:

- **Error Tracking**: Automatic capture of exceptions and errors
- **Performance Monitoring**: Track slow database queries, API calls, and transactions
- **User Context**: Associate errors with users and requests
- **Breadcrumbs**: Track events leading up to errors
- **Custom Errors**: Business logic errors with proper categorization
- **Security**: Automatic filtering of sensitive data

## Backend Setup (FastAPI)

### Installation

Add Sentry SDK to `requirements.txt`:

```bash
sentry-sdk[fastapi]>=2.0.0
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### Configuration

1. **Set Environment Variables**

Add to your `.env` file or environment:

```bash
SENTRY_DSN=https://your-dsn@sentry.io/project-id
SENTRY_RELEASE=1.0.0
ENVIRONMENT=production
```

2. **Initialize Sentry**

Sentry is automatically initialized in `app/main.py` when the application starts. The initialization happens in `app/sentry_config.py`.

### Usage Examples

#### Basic Error Tracking

```python
from app.sentry_config import capture_exception, add_breadcrumb

try:
    # Your code
    result = some_operation()
except Exception as e:
    capture_exception(e)
    raise
```

#### Custom Exceptions

```python
from app.exceptions import StoryGenerationError, LLMAPIError

# Business logic error
try:
    outline = generate_story_outline(premise)
except Exception as e:
    raise StoryGenerationError(
        message="Failed to generate story outline",
        premise=premise,
        genre=genre
    )

# LLM API error
try:
    response = await llm_client.generate(prompt)
except httpx.HTTPStatusError as e:
    raise LLMAPIError(
        message="LLM API call failed",
        api_url=api_url,
        status_code=e.response.status_code,
        response_body=e.response.text
    )
```

#### Adding Context

```python
from app.sentry_config import set_user_context, set_request_context

# Set user context
set_user_context(
    user_id=123,
    email="user@example.com",
    username="johndoe"
)

# Set request context
set_request_context(
    request_id=request_id,
    story_id=story_id,
    operation="generate_outline"
)

# Add breadcrumbs
add_breadcrumb(
    message="Starting story generation",
    category="story_generation",
    level="info",
    data={"premise": premise, "genre": genre}
)
```

#### Performance Tracking

```python
from app.sentry_config import start_transaction

# Track database query
with start_transaction(name="db_query", op="db.query") as transaction:
    with transaction.start_child(op="db.query", description="SELECT stories"):
        stories = await db.query_stories()
```

#### Using in Endpoints

```python
@app.post('/generate_outline')
async def generate_outline(req: OutlineReq, request: Request):
    # Request ID is automatically set by middleware
    request_id = request.state.request_id
    
    # Set story context
    set_request_context(request_id=request_id, operation="generate_outline")
    
    try:
        # Your logic
        outline = await generate_story(req.premise)
        return outline
    except StoryGenerationError as e:
        # Custom exception automatically captured
        raise
    except Exception as e:
        # General exception captured by exception handler
        raise
```

## Frontend Setup (React)

### Installation

Install Sentry packages:

```bash
npm install @sentry/react @sentry/tracing
```

### Configuration

1. **Set Environment Variables**

Create `.env` file in `frontend/`:

```bash
VITE_SENTRY_DSN=https://your-dsn@sentry.io/project-id
VITE_SENTRY_RELEASE=1.0.0
```

2. **Initialize Sentry**

Sentry is initialized in `src/main.tsx`:

```typescript
import { initSentry } from './lib/sentry';

// Initialize before rendering
initSentry();
```

3. **Wrap App with ErrorBoundary**

```typescript
import { ErrorBoundary } from './components/ErrorBoundary';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>
);
```

### Usage Examples

#### Setting User Context

```typescript
import { setUserContext, clearUserContext } from './lib/sentry';

// On login
function handleLogin(user: User) {
  setUserContext(user.id, user.email, user.username);
}

// On logout
function handleLogout() {
  clearUserContext();
}
```

#### Tracking API Calls

```typescript
import { trackAPICall } from './lib/sentry';
import { api } from './lib/api';

// API calls are automatically tracked via axios interceptors
// Or manually track custom calls:
const data = await trackAPICall(
  () => api.post('/generate_outline', { premise }),
  '/generate_outline',
  'POST'
);
```

#### Adding Breadcrumbs

```typescript
import { addBreadcrumb } from './lib/sentry';

addBreadcrumb(
  'User clicked generate button',
  'user_action',
  'info',
  { storyId: 123 }
);
```

#### Setting Tags

```typescript
import { setTag } from './lib/sentry';

setTag('story_id', '123');
setTag('feature', 'story_generation');
```

#### Capturing Exceptions

```typescript
import { captureException } from './lib/sentry';

try {
  await someAsyncOperation();
} catch (error) {
  captureException(error as Error, {
    context: 'story_generation',
    storyId: 123,
  });
}
```

#### User Feedback

```typescript
import { showFeedbackDialog } from './lib/sentry';

// Show feedback dialog on error
function handleError(error: Error) {
  captureException(error);
  showFeedbackDialog();
}
```

#### Using Error Boundary

```typescript
import { ErrorBoundary } from './components/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary
      onError={(error, errorInfo) => {
        console.error('Error caught by boundary:', error);
      }}
    >
      <YourApp />
    </ErrorBoundary>
  );
}
```

## Custom Error Classes

### Backend Custom Errors

Located in `app/exceptions.py`:

- **`StoryGenerationError`**: Story generation failures
- **`LLMAPIError`**: LLM API call failures
- **`RateLimitError`**: Rate limiting errors (429)
- **`DatabaseConnectionError`**: Database connection failures
- **`VectorStoreError`**: Vector store operation errors
- **`ValidationError`**: Input validation errors

Usage:

```python
from app.exceptions import StoryGenerationError

try:
    outline = generate_outline(premise)
except Exception as e:
    raise StoryGenerationError(
        message="Failed to generate outline",
        premise=premise,
        genre=genre
    )
```

## Alerting Configuration

Configure alerts in Sentry dashboard:

### 1. Production Errors (Slack)

**Settings**: Alerts > Create Alert Rule

- **Conditions**: Issue frequency > 10 in 5 minutes, Environment = production
- **Actions**: Send to Slack channel
- **Filters**: Error level = error

### 2. Critical Issues (Email)

**Settings**: Alerts > Create Alert Rule

- **Conditions**: Issue first seen, Tags contains critical
- **Actions**: Send email to team
- **Filters**: Environment = production

### 3. Weekly Digest (Email)

**Settings**: Alerts > Create Alert Rule

- **Conditions**: Weekly digest
- **Actions**: Send email digest
- **Schedule**: Every Monday at 9 AM

### 4. Rate Limiting (Slack)

**Settings**: Alerts > Create Alert Rule

- **Conditions**: Issue frequency > 5 in 1 minute, Tags contains rate_limit
- **Actions**: Send to Slack channel
- **Filters**: Environment = production

## Source Maps (Frontend)

For readable stack traces in production:

1. **Build with source maps**:

```bash
npm run build
```

2. **Upload source maps** (add to build script):

```json
{
  "scripts": {
    "build": "vite build",
    "upload-sourcemaps": "sentry-cli sourcemaps inject ./dist && sentry-cli sourcemaps upload ./dist"
  }
}
```

Or use Sentry Vite plugin:

```bash
npm install @sentry/vite-plugin
```

Configure in `vite.config.ts`:

```typescript
import { sentryVitePlugin } from "@sentry/vite-plugin";

export default defineConfig({
  plugins: [
    sentryVitePlugin({
      org: "your-org",
      project: "storyweave-frontend",
      authToken: process.env.SENTRY_AUTH_TOKEN,
    }),
  ],
});
```

## Performance Monitoring

### Backend

Database queries and API calls are automatically tracked via Sentry integrations.

### Frontend

Transaction tracking is enabled. Monitor:

- Page loads
- API calls
- User interactions
- Route changes

## Security Best Practices

1. **Never commit DSNs** to version control
2. **Use environment variables** for all Sentry configuration
3. **Filter sensitive data** - Already configured in `before_send` hooks
4. **Limit PII** - `send_default_pii=False` by default
5. **Review alerts** - Ensure no sensitive data leaks through

## Troubleshooting

### Backend Issues

**Sentry not initializing:**
- Check `SENTRY_DSN` environment variable
- Check logs for initialization messages

**Errors not appearing:**
- Verify DSN is correct
- Check network connectivity to Sentry
- Review `before_send` filter logic

### Frontend Issues

**Sentry not initializing:**
- Check `VITE_SENTRY_DSN` environment variable
- Check browser console for warnings

**Source maps not working:**
- Verify source maps are uploaded
- Check release version matches

## Environment Variables Reference

### Backend

```bash
SENTRY_DSN=https://your-dsn@sentry.io/project-id
SENTRY_RELEASE=1.0.0
ENVIRONMENT=production
```

### Frontend

```bash
VITE_SENTRY_DSN=https://your-dsn@sentry.io/project-id
VITE_SENTRY_RELEASE=1.0.0
```

## Next Steps

1. **Set up Sentry projects** for backend and frontend
2. **Configure environment variables** in your deployment
3. **Set up alerting rules** in Sentry dashboard
4. **Test error tracking** by triggering test errors
5. **Configure source maps** for production frontend builds
6. **Set up releases** to track deployments

## Additional Resources

- [Sentry Documentation](https://docs.sentry.io/)
- [FastAPI Integration](https://docs.sentry.io/platforms/python/guides/fastapi/)
- [React Integration](https://docs.sentry.io/platforms/javascript/guides/react/)
- [Performance Monitoring](https://docs.sentry.io/product/performance/)
