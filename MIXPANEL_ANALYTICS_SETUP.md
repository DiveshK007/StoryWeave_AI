# Mixpanel Analytics Integration Guide

Complete guide for using Mixpanel product analytics in StoryWeave AI.

## Overview

Mixpanel provides comprehensive product analytics to track user behavior, feature usage, and business metrics. This integration includes:

- **Event Tracking**: Track user actions and events
- **User Properties**: Store user attributes and behavior
- **Funnel Analysis**: Understand user conversion
- **Cohort Analysis**: Group users by behavior
- **Real-time Analytics**: Monitor events as they happen
- **GDPR Compliance**: Privacy-first tracking with consent

## Quick Start

### 1. Get Mixpanel Credentials

1. Sign up at [mixpanel.com](https://mixpanel.com)
2. Create a new project
3. Get your **Project Token** (for tracking events)
4. Get your **API Secret** (for admin analytics API)

### 2. Configure Backend

Add to `agentic-aws-nvidia-demo/services/orchestrator/.env`:

```bash
MIXPANEL_TOKEN=your_project_token_here
MIXPANEL_API_SECRET=your_api_secret_here
APP_VERSION=1.0.0
ENVIRONMENT=production
```

### 3. Configure Frontend

Create `frontend/.env`:

```bash
VITE_MIXPANEL_TOKEN=your_project_token_here
VITE_APP_VERSION=1.0.0
```

### 4. Install Dependencies

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

## Backend Usage

### Import Analytics Functions

```python
from app.analytics import (
    track_user_registered,
    track_story_created,
    track_outline_generated,
    track_scene_expanded,
    track_story_exported,
    track_error_occurred,
    update_user_last_active,
    set_user_subscription_tier,
    set_user_favorite_genre
)
```

### Track User Registration

```python
from app.analytics import track_user_registered

@app.post('/register')
async def register(user_data: UserRegistration):
    user = await create_user(user_data)
    
    # Track registration
    track_user_registered(
        user_id=user.id,
        email=user.email,
        source="web"  # or "mobile", "api", etc.
    )
    
    return user
```

### Track Story Creation

```python
from app.analytics import track_story_created

@app.post('/stories')
async def create_story(story_data: StoryCreate):
    story = await db.create_story(story_data)
    
    track_story_created(
        user_id=story.user_id,
        story_id=story.id,
        genre=story.genre,
        length=story.length,
        has_corpus=bool(story.corpus_id)
    )
    
    return story
```

### Track Outline Generation

```python
from app.analytics import track_outline_generated
import time

@app.post('/generate_outline')
async def generate_outline(req: OutlineReq):
    start_time = time.time()
    
    try:
        outline = await generate_story_outline(req.premise)
        generation_time = time.time() - start_time
        
        track_outline_generated(
            user_id=current_user.id,
            story_id=outline.story_id,
            generation_time=generation_time,
            beat_count=len(outline.beats),
            genre=req.genre
        )
        
        return outline
    except Exception as e:
        track_error_occurred(
            user_id=current_user.id,
            error_type="outline_generation_failed",
            endpoint="/generate_outline",
            error_message=str(e)
        )
        raise
```

### Track Scene Expansion

```python
from app.analytics import track_scene_expanded

@app.post('/expand_scene')
async def expand_scene(req: SceneExpandReq):
    start_time = time.time()
    
    scene = await generate_scene(req)
    generation_time = time.time() - start_time
    
    track_scene_expanded(
        user_id=current_user.id,
        story_id=req.story_id,
        beat_index=req.beat_index,
        scene_length=len(scene.content),
        generation_time=generation_time
    )
    
    return scene
```

### Track Story Export

```python
from app.analytics import track_story_exported

@app.post('/export')
async def export_story(req: ExportReq):
    exported_data = await export_story_to_file(req.story_id, req.format)
    
    track_story_exported(
        user_id=current_user.id,
        story_id=req.story_id,
        format=req.format,  # "txt", "pdf", "docx"
        scene_count=len(exported_data.scenes),
        total_length=len(exported_data.content)
    )
    
    return exported_data
```

### Update User Properties

```python
from app.analytics import (
    update_user_last_active,
    set_user_subscription_tier,
    set_user_favorite_genre
)

# Update last active (call on each request)
@app.middleware("http")
async def update_activity(request: Request, call_next):
    if current_user:
        update_user_last_active(current_user.id)
    return await call_next(request)

# Set subscription tier
set_user_subscription_tier(user_id=123, tier="pro")

# Update favorite genre
set_user_favorite_genre(user_id=123, genre="Science Fiction")
```

### Track Errors

```python
from app.analytics import track_error_occurred

@app.exception_handler(Exception)
async def error_handler(request: Request, exc: Exception):
    user_id = getattr(request.state, "user_id", None)
    
    track_error_occurred(
        user_id=user_id,
        error_type=type(exc).__name__,
        endpoint=request.url.path,
        error_message=str(exc)
    )
    
    # ... handle error
```

## Frontend Usage

### Import Analytics Functions

```typescript
import {
  trackPageView,
  trackButtonClick,
  trackFeatureUsed,
  trackSearchPerformed,
  trackTutorialCompleted,
  identify,
  setUserProperties,
  trackStoryCreated,
  trackOutlineGenerated,
} from './lib/analytics';
```

### Track Page Views

```typescript
import { usePageView } from './hooks/useAnalytics';

function StoryEditor() {
  usePageView('Story Editor');
  
  return <div>...</div>;
}
```

### Track Button Clicks

```typescript
import { useButtonTracking } from './hooks/useAnalytics';

function MyComponent() {
  const trackButton = useButtonTracking();
  
  return (
    <button onClick={() => {
      trackButton('Generate Story', '/editor');
      // ... handle click
    }}>
      Generate
    </button>
  );
}
```

### Track Feature Usage

```typescript
import { useFeatureTracking } from './hooks/useAnalytics';

function StoryGenerator() {
  const { trackStart, trackEnd } = useFeatureTracking('story_generation');
  
  const handleGenerate = async () => {
    trackStart();
    
    try {
      const story = await generateStory();
      trackEnd({ success: true, story_id: story.id });
    } catch (error) {
      trackEnd({ success: false, error: error.message });
    }
  };
  
  return <button onClick={handleGenerate}>Generate</button>;
}
```

### Track Search

```typescript
import { useSearchTracking } from './hooks/useAnalytics';

function CorpusSearch() {
  const trackSearch = useSearchTracking();
  const [results, setResults] = useState([]);
  
  const handleSearch = async (query: string) => {
    const results = await searchCorpus(query);
    setResults(results);
    
    // Track search (debounced automatically)
    trackSearch(query, results.length);
  };
  
  return <SearchInput onSearch={handleSearch} />;
}
```

### Identify Users

```typescript
import { identify, trackUserRegistered } from './lib/analytics';

// On login/registration
function handleLogin(user: User) {
  identify(user.id.toString(), {
    email: user.email,
    username: user.username,
  });
  
  trackUserRegistered(user.id.toString(), 'web');
}

// On logout
import { reset } from './lib/analytics';
reset();
```

### Track Story Events

```typescript
import { trackStoryCreated, trackOutlineGenerated } from './lib/analytics';

// When story is created
trackStoryCreated(storyId, genre, { has_corpus: true });

// When outline is generated
const startTime = Date.now();
const outline = await generateOutline();
const generationTime = (Date.now() - startTime) / 1000;

trackOutlineGenerated(storyId, generationTime, outline.beats.length, genre);
```

### Track Tutorial Completion

```typescript
import { useTutorialTracking } from './hooks/useAnalytics';

function Tutorial() {
  const { trackStart, trackStep, trackComplete } = useTutorialTracking('onboarding');
  
  useEffect(() => {
    trackStart();
  }, []);
  
  const handleStepComplete = (stepNumber: number) => {
    trackStep(`Step ${stepNumber}`, stepNumber);
  };
  
  const handleTutorialComplete = () => {
    trackComplete({ steps_completed: 5 });
  };
  
  return <TutorialSteps onStepComplete={handleStepComplete} />;
}
```

## Admin Dashboard

### Access Admin Analytics

The admin dashboard is available at `/admin/analytics` endpoints:

- `GET /admin/analytics/overview?days=7` - Overview metrics
- `GET /admin/analytics/genres?days=30` - Genre popularity
- `GET /admin/analytics/funnel` - Feature usage funnel
- `GET /admin/analytics/users?days=7` - User analytics
- `GET /admin/analytics/errors?days=7` - Error analytics

### Use Admin Analytics Component

```typescript
import { AdminAnalytics } from './components/AdminAnalytics';

function AdminDashboard() {
  return <AdminAnalytics />;
}
```

## Privacy & GDPR Compliance

### Consent Banner

The `AnalyticsConsent` component is automatically included in the app and shows on first visit. Users can:

- Accept analytics tracking
- Decline tracking
- Dismiss for later

The consent preference is stored in `localStorage` and respected throughout the app.

### Opt-Out Mechanism

Users can opt out at any time:

```typescript
import { setAnalyticsEnabled } from './lib/analytics';

// Disable analytics
setAnalyticsEnabled(false);

// Re-enable analytics
setAnalyticsEnabled(true);
```

### Anonymous Tracking

Analytics respects Do Not Track (DNT) browser settings. When DNT is enabled, Mixpanel tracking is disabled.

### Data Retention

Mixpanel data retention is set to 90 days by default. Configure in your Mixpanel project settings.

## Event Naming Convention

### Backend Events

- `user_registered` - User registration
- `story_created` - Story creation
- `outline_generated` - Outline generation
- `scene_expanded` - Scene expansion
- `story_exported` - Story export
- `error_occurred` - Error tracking
- `api_call` - API performance tracking

### Frontend Events

- `page_viewed` - Page navigation
- `button_clicked` - Button interactions
- `feature_used` - Feature usage with duration
- `search_performed` - Search queries
- `tutorial_completed` - Tutorial completion
- `form_submitted` - Form submissions
- `form_abandoned` - Form abandonment

## User Properties

The following user properties are automatically tracked:

- `signup_date` - User registration date
- `total_stories_created` - Number of stories created
- `favorite_genre` - Most used genre
- `last_active` - Last activity timestamp
- `subscription_tier` - User subscription level

## Best Practices

1. **Track Meaningful Events**: Focus on events that drive business decisions
2. **Use Consistent Naming**: Follow the naming convention
3. **Include Context**: Add relevant properties to events
4. **Respect Privacy**: Always get user consent
5. **Test Events**: Verify events in Mixpanel dashboard
6. **Monitor Performance**: Don't track too many events
7. **Document Events**: Keep a list of all tracked events

## Troubleshooting

### Events Not Appearing in Mixpanel

1. Check `MIXPANEL_TOKEN` is set correctly
2. Verify network connectivity
3. Check browser console for errors
4. Verify user consent is given

### Admin Analytics Not Working

1. Check `MIXPANEL_API_SECRET` is set
2. Verify API secret has correct permissions
3. Check backend logs for API errors

### Performance Issues

1. Reduce event frequency
2. Use batch tracking for high-volume events
3. Debounce search/typing events
4. Disable tracking in development

## Additional Resources

- [Mixpanel Documentation](https://docs.mixpanel.com/)
- [Mixpanel JavaScript SDK](https://developer.mixpanel.com/docs/javascript-full-api-reference)
- [Mixpanel Python SDK](https://github.com/mixpanel/mixpanel-python)
