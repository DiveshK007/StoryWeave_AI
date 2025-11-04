/**
 * Mixpanel analytics integration for StoryWeave AI frontend.
 * 
 * Provides event tracking, user property management, and React hooks.
 */
import mixpanel from 'mixpanel-browser';

let isInitialized = false;
let analyticsEnabled = true;

// Get Mixpanel token from environment
const MIXPANEL_TOKEN = import.meta.env.VITE_MIXPANEL_TOKEN;
const APP_VERSION = import.meta.env.VITE_APP_VERSION || '1.0.0';

/**
 * Initialize Mixpanel.
 */
export function initMixpanel(token?: string, enabled: boolean = true): void {
  if (isInitialized) {
    console.warn('Mixpanel already initialized');
    return;
  }

  const mpToken = token || MIXPANEL_TOKEN;
  analyticsEnabled = enabled;

  if (!mpToken) {
    console.warn('Mixpanel token not provided. Analytics disabled.');
    analyticsEnabled = false;
    return;
  }

  if (!enabled) {
    console.log('Analytics disabled by user preference');
    analyticsEnabled = false;
    return;
  }

  try {
    mixpanel.init(mpToken, {
      debug: import.meta.env.DEV,
      track_pageview: true,
      persistence: 'localStorage',
      ignore_dnt: false, // Respect Do Not Track
    });
    isInitialized = true;
    console.log('Mixpanel initialized successfully');
  } catch (error) {
    console.error('Failed to initialize Mixpanel:', error);
    analyticsEnabled = false;
  }
}

/**
 * Enable or disable analytics.
 */
export function setAnalyticsEnabled(enabled: boolean): void {
  analyticsEnabled = enabled;
  if (enabled && !isInitialized) {
    initMixpanel();
  }
  // Store preference
  localStorage.setItem('analytics_enabled', enabled.toString());
}

/**
 * Check if analytics is enabled.
 */
export function isAnalyticsEnabled(): boolean {
  if (!analyticsEnabled) return false;
  // Check localStorage preference
  const stored = localStorage.getItem('analytics_enabled');
  if (stored !== null) {
    return stored === 'true';
  }
  return analyticsEnabled;
}

/**
 * Track an event with properties.
 */
export function track(
  eventName: string,
  properties?: Record<string, any>
): void {
  if (!isAnalyticsEnabled() || !isInitialized) {
    return;
  }

  try {
    const defaultProperties = {
      app_version: APP_VERSION,
      timestamp: new Date().toISOString(),
      page: window.location.pathname,
    };

    mixpanel.track(eventName, {
      ...defaultProperties,
      ...properties,
    });
  } catch (error) {
    console.error(`Failed to track event ${eventName}:`, error);
  }
}

/**
 * Identify a user.
 */
export function identify(userId: string, userProperties?: Record<string, any>): void {
  if (!isAnalyticsEnabled() || !isInitialized) {
    return;
  }

  try {
    mixpanel.identify(userId);
    if (userProperties) {
      mixpanel.people.set(userProperties);
    }
  } catch (error) {
    console.error('Failed to identify user:', error);
  }
}

/**
 * Reset user identity (on logout).
 */
export function reset(): void {
  if (!isInitialized) {
    return;
  }

  try {
    mixpanel.reset();
  } catch (error) {
    console.error('Failed to reset user:', error);
  }
}

/**
 * Set user properties.
 */
export function setUserProperties(properties: Record<string, any>): void {
  if (!isAnalyticsEnabled() || !isInitialized) {
    return;
  }

  try {
    mixpanel.people.set(properties);
  } catch (error) {
    console.error('Failed to set user properties:', error);
  }
}

/**
 * Increment user property.
 */
export function incrementUserProperty(property: string, value: number = 1): void {
  if (!isAnalyticsEnabled() || !isInitialized) {
    return;
  }

  try {
    mixpanel.people.increment(property, value);
  } catch (error) {
    console.error(`Failed to increment property ${property}:`, error);
  }
}

// Event Tracking Functions

/**
 * Track page view.
 */
export function trackPageView(pageName: string, properties?: Record<string, any>): void {
  track('page_viewed', {
    page_name: pageName,
    ...properties,
  });
}

/**
 * Track button click.
 */
export function trackButtonClick(
  buttonName: string,
  page?: string,
  properties?: Record<string, any>
): void {
  track('button_clicked', {
    button_name: buttonName,
    page: page || window.location.pathname,
    ...properties,
  });
}

/**
 * Track feature usage.
 */
export function trackFeatureUsed(
  featureName: string,
  duration?: number,
  properties?: Record<string, any>
): void {
  const eventProperties: Record<string, any> = {
    feature_name: featureName,
    ...properties,
  };

  if (duration !== undefined) {
    eventProperties.duration = duration;
  }

  track('feature_used', eventProperties);
}

/**
 * Track search performed.
 */
export function trackSearchPerformed(
  query: string,
  resultCount?: number,
  properties?: Record<string, any>
): void {
  track('search_performed', {
    query_length: query.length,
    result_count: resultCount,
    ...properties,
  });
}

/**
 * Track tutorial completion.
 */
export function trackTutorialCompleted(
  tutorialName: string,
  duration?: number,
  properties?: Record<string, any>
): void {
  const eventProperties: Record<string, any> = {
    tutorial_name: tutorialName,
    ...properties,
  };

  if (duration !== undefined) {
    eventProperties.duration = duration;
  }

  track('tutorial_completed', eventProperties);
}

/**
 * Track story creation (frontend).
 */
export function trackStoryCreated(
  storyId: number,
  genre?: string,
  properties?: Record<string, any>
): void {
  track('story_created', {
    story_id: storyId,
    genre: genre || 'unknown',
    ...properties,
  });
}

/**
 * Track outline generation (frontend).
 */
export function trackOutlineGenerated(
  storyId: number,
  generationTime: number,
  beatCount: number,
  properties?: Record<string, any>
): void {
  track('outline_generated', {
    story_id: storyId,
    generation_time: generationTime,
    beat_count: beatCount,
    ...properties,
  });
}

/**
 * Track error occurrence (frontend).
 */
export function trackError(
  errorType: string,
  errorMessage?: string,
  properties?: Record<string, any>
): void {
  track('error_occurred', {
    error_type: errorType,
    error_message: errorMessage?.substring(0, 200), // Limit length
    page: window.location.pathname,
    ...properties,
  });
}

/**
 * Track user registration (frontend).
 */
export function trackUserRegistered(
  userId: string,
  source?: string,
  properties?: Record<string, any>
): void {
  identify(userId);
  track('user_registered', {
    source: source || 'unknown',
    ...properties,
  });

  // Set initial user properties
  setUserProperties({
    signup_date: new Date().toISOString(),
    total_stories_created: 0,
    last_active: new Date().toISOString(),
  });
}

/**
 * Update user last active.
 */
export function updateLastActive(): void {
  setUserProperties({
    last_active: new Date().toISOString(),
  });
}

/**
 * Set user subscription tier.
 */
export function setSubscriptionTier(tier: string): void {
  setUserProperties({
    subscription_tier: tier,
  });
}

/**
 * Track custom event with automatic properties.
 */
export function trackCustom(
  eventName: string,
  properties?: Record<string, any>
): void {
  track(eventName, properties);
}

// Initialize on load (respecting user preferences)
if (typeof window !== 'undefined') {
  const consent = localStorage.getItem('analytics_consent');
  if (consent === 'true') {
    initMixpanel();
  }
}
