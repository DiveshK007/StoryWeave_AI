/**
 * React hooks for Mixpanel analytics.
 */
import { useEffect, useCallback, useRef } from 'react';
import {
  track,
  trackPageView,
  trackButtonClick,
  trackFeatureUsed,
  trackSearchPerformed,
  trackTutorialCompleted,
  trackCustom,
  setUserProperties,
  updateLastActive,
  isAnalyticsEnabled,
} from '../lib/analytics';

/**
 * Hook to track page views automatically.
 */
export function usePageView(pageName: string, properties?: Record<string, any>): void {
  useEffect(() => {
    trackPageView(pageName, properties);
  }, [pageName]);
}

/**
 * Hook to track feature usage with duration.
 */
export function useFeatureTracking(featureName: string) {
  const startTime = useRef<number>(Date.now());

  const trackStart = useCallback(() => {
    startTime.current = Date.now();
  }, []);

  const trackEnd = useCallback((properties?: Record<string, any>) => {
    const duration = Date.now() - startTime.current;
    trackFeatureUsed(featureName, duration, properties);
  }, [featureName]);

  return { trackStart, trackEnd };
}

/**
 * Hook to track button clicks easily.
 */
export function useButtonTracking() {
  return useCallback((
    buttonName: string,
    page?: string,
    properties?: Record<string, any>
  ) => {
    trackButtonClick(buttonName, page, properties);
  }, []);
}

/**
 * Hook to track search with debouncing.
 */
export function useSearchTracking() {
  const searchTimeout = useRef<NodeJS.Timeout>();

  return useCallback((
    query: string,
    resultCount?: number,
    properties?: Record<string, any>
  ) => {
    // Debounce search tracking (only track after 500ms of no typing)
    if (searchTimeout.current) {
      clearTimeout(searchTimeout.current);
    }

    searchTimeout.current = setTimeout(() => {
      if (query.trim().length > 0) {
        trackSearchPerformed(query, resultCount, properties);
      }
    }, 500);
  }, []);
}

/**
 * Hook to update user last active periodically.
 */
export function useLastActiveTracking(intervalMs: number = 60000): void {
  useEffect(() => {
    if (!isAnalyticsEnabled()) return;

    // Update immediately
    updateLastActive();

    // Update periodically
    const interval = setInterval(() => {
      updateLastActive();
    }, intervalMs);

    return () => clearInterval(interval);
  }, [intervalMs]);
}

/**
 * Hook to track custom events easily.
 */
export function useTrack() {
  return useCallback((
    eventName: string,
    properties?: Record<string, any>
  ) => {
    trackCustom(eventName, properties);
  }, []);
}

/**
 * Hook to track tutorial progress.
 */
export function useTutorialTracking(tutorialName: string) {
  const startTime = useRef<number>(Date.now());

  const trackStart = useCallback(() => {
    startTime.current = Date.now();
  }, []);

  const trackStep = useCallback((stepName: string, stepNumber: number) => {
    track('tutorial_step_completed', {
      tutorial_name: tutorialName,
      step_name: stepName,
      step_number: stepNumber,
    });
  }, [tutorialName]);

  const trackComplete = useCallback((properties?: Record<string, any>) => {
    const duration = Date.now() - startTime.current;
    trackTutorialCompleted(tutorialName, duration, properties);
  }, [tutorialName]);

  return { trackStart, trackStep, trackComplete };
}

/**
 * Hook to track form interactions.
 */
export function useFormTracking(formName: string) {
  const startTime = useRef<number>(Date.now());
  const fieldInteractions = useRef<Set<string>>(new Set());

  const trackFieldFocus = useCallback((fieldName: string) => {
    fieldInteractions.current.add(fieldName);
  }, []);

  const trackSubmit = useCallback((success: boolean, properties?: Record<string, any>) => {
    const duration = Date.now() - startTime.current;
    track('form_submitted', {
      form_name: formName,
      success,
      duration,
      fields_interacted: fieldInteractions.current.size,
      ...properties,
    });
  }, [formName]);

  const trackAbandon = useCallback(() => {
    const duration = Date.now() - startTime.current;
    track('form_abandoned', {
      form_name: formName,
      duration,
      fields_interacted: fieldInteractions.current.size,
    });
  }, [formName]);

  useEffect(() => {
    startTime.current = Date.now();
    return () => {
      // Track abandonment if form unmounts without submit
      if (fieldInteractions.current.size > 0) {
        trackAbandon();
      }
    };
  }, [formName, trackAbandon]);

  return { trackFieldFocus, trackSubmit };
}
