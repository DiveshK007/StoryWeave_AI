# Sentry Quick Start Guide

This guide will help you get Sentry error tracking up and running in 5 minutes.

## ✅ Integration Status

All Sentry integration files have been created:

### Backend Files
- ✅ `app/sentry_config.py` - Sentry initialization and utilities
- ✅ `app/exceptions.py` - Custom error classes
- ✅ `app/main.py` - Sentry middleware and exception handlers
- ✅ `app/settings.py` - Sentry DSN configuration
- ✅ `requirements.txt` - Sentry SDK dependency

### Frontend Files
- ✅ `src/lib/sentry.ts` - Sentry configuration
- ✅ `src/components/ErrorBoundary.tsx` - Error boundary component
- ✅ `src/main.tsx` - Sentry initialization
- ✅ `src/lib/api.ts` - API client with Sentry tracking
- ✅ `package.json` - Sentry dependencies

## 🚀 Quick Setup (5 Minutes)

### Step 1: Install Dependencies

**Backend:**
```bash
cd agentic-aws-nvidia-demo/services/orchestrator
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### Step 2: Get Sentry DSN

1. Go to [sentry.io](https://sentry.io) and sign up/login
2. Create a new project (one for backend, one for frontend)
3. Select **FastAPI** for backend project
4. Select **React** for frontend project
5. Copy the DSN from each project

### Step 3: Configure Environment Variables

**Backend** - Add to `.env` or environment:
```bash
SENTRY_DSN=https://your-backend-dsn@sentry.io/project-id
SENTRY_RELEASE=1.0.0
ENVIRONMENT=production  # or development, staging
```

**Frontend** - Create `frontend/.env`:
```bash
VITE_SENTRY_DSN=https://your-frontend-dsn@sentry.io/project-id
VITE_SENTRY_RELEASE=1.0.0
```

### Step 4: Test the Integration

**Backend Test:**
```python
# Add this to any endpoint to test
from app.sentry_config import capture_exception

@app.get("/test-sentry")
async def test_sentry():
    try:
        raise ValueError("This is a test error!")
    except Exception as e:
        capture_exception(e)
        return {"message": "Error captured in Sentry"}
```

**Frontend Test:**
```typescript
// Add this button to test
<button onClick={() => {
  throw new Error("Test error from frontend!");
}}>
  Test Sentry
</button>
```

### Step 5: Verify in Sentry Dashboard

1. Go to your Sentry project dashboard
2. Trigger the test errors above
3. You should see events appear within seconds

## 📋 Integration Checklist

### Backend Integration ✅
- [x] Sentry SDK initialized in `main.py`
- [x] Exception handlers configured
- [x] Request context middleware (request_id, story_id)
- [x] Custom exception classes with Sentry integration
- [x] Performance tracking enabled
- [x] Breadcrumbs configured
- [x] Sensitive data filtering

### Frontend Integration ✅
- [x] Sentry initialized in `main.tsx`
- [x] Error Boundary component created
- [x] API error tracking in interceptors
- [x] User context management
- [x] Performance monitoring
- [x] Session Replay ready
- [x] User Feedback widget ready

### Custom Error Tracking ✅
- [x] StoryGenerationError class
- [x] LLMAPIError class
- [x] RateLimitError class
- [x] DatabaseConnectionError class
- [x] VectorStoreError class
- [x] ValidationError class

### Alerting Configuration ⚠️
- [ ] Set up Slack integration in Sentry
- [ ] Configure email alerts
- [ ] Create alert rules (see SENTRY_SETUP.md)

## 🎯 Common Use Cases

### Backend: Using Custom Exceptions

```python
from app.exceptions import StoryGenerationError, LLMAPIError

@app.post('/generate_outline')
async def generate_outline(req: OutlineReq):
    try:
        # Your logic
        outline = await generate_story(req.premise)
        return outline
    except Exception as e:
        # This will automatically capture to Sentry
        raise StoryGenerationError(
            message="Failed to generate outline",
            premise=req.premise,
            genre=req.genre
        )
```

### Frontend: Tracking API Errors

```typescript
import { api } from './lib/api';

// Errors are automatically tracked!
try {
  const result = await api.post('/generate_outline', { premise });
} catch (error) {
  // Already captured to Sentry via interceptor
  console.error(error);
}
```

### Frontend: Setting User Context

```typescript
import { setUserContext } from './lib/sentry';

// When user logs in
setUserContext(user.id, user.email, user.username);
```

### Adding Breadcrumbs

**Backend:**
```python
from app.sentry_config import add_breadcrumb

add_breadcrumb(
    message="Starting story generation",
    category="story_generation",
    level="info",
    data={"premise": premise, "genre": genre}
)
```

**Frontend:**
```typescript
import { addBreadcrumb } from './lib/sentry';

addBreadcrumb(
  'User clicked generate button',
  'user_action',
  'info',
  { storyId: 123 }
);
```

## 🔧 Troubleshooting

### Backend: No Events in Sentry
1. Check `SENTRY_DSN` is set correctly
2. Check logs for "Sentry initialized" message
3. Verify network connectivity to Sentry
4. Check `before_send` filter isn't blocking events

### Frontend: No Events in Sentry
1. Check `VITE_SENTRY_DSN` is set correctly
2. Check browser console for warnings
3. Verify `initSentry()` is called before rendering
4. Check network tab for Sentry API calls

### Source Maps Not Working
1. Ensure source maps are generated in build
2. Upload source maps to Sentry (see SENTRY_SETUP.md)
3. Verify release version matches

## 📚 Next Steps

1. **Set up Alerting** - See `SENTRY_SETUP.md` for alert configuration
2. **Configure Source Maps** - For readable production stack traces
3. **Set up Environments** - Separate dev/staging/prod projects
4. **Review Error Grouping** - Customize fingerprinting if needed

## 📖 Full Documentation

For detailed documentation, see:
- **`SENTRY_SETUP.md`** - Complete setup guide with examples
- **`frontend/src/examples/sentry-usage.example.tsx`** - Frontend examples
- **Sentry Docs** - https://docs.sentry.io/

## 🆘 Need Help?

1. Check `SENTRY_SETUP.md` for detailed examples
2. Review Sentry dashboard for event details
3. Check application logs for initialization messages
4. Verify environment variables are set correctly
