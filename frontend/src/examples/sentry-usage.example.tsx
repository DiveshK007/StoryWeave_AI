/**
 * Example: Using Sentry for error tracking and monitoring
 * 
 * This file demonstrates various ways to use Sentry in your React components.
 */

import React, { useState, useEffect } from 'react';
import {
  setUserContext,
  clearUserContext,
  addBreadcrumb,
  setTag,
  setContext,
  captureException,
  captureMessage,
  trackAPICall,
  showFeedbackDialog,
} from '../lib/sentry';
import { apiCall } from '../lib/api';

// Example 1: Setting user context on login
export function LoginExample() {
  const handleLogin = async (email: string, password: string) => {
    try {
      // Add breadcrumb for login attempt
      addBreadcrumb('User attempting login', 'auth', 'info', { email });

      const response = await apiCall('POST', '/auth/login', { email, password });
      
      // Set user context after successful login
      setUserContext(response.user.id, response.user.email, response.user.username);
      
      // Set tags for filtering
      setTag('user_role', response.user.role);
      setTag('subscription', response.user.subscription);
      
      addBreadcrumb('User logged in successfully', 'auth', 'info', {
        userId: response.user.id,
      });

      return response;
    } catch (error) {
      captureException(error as Error, {
        context: 'login',
        email,
        error_type: 'authentication_error',
      });
      throw error;
    }
  };

  const handleLogout = () => {
    addBreadcrumb('User logged out', 'auth', 'info');
    clearUserContext();
  };

  return null; // Example component
}

// Example 2: Tracking story generation with context
export function StoryGenerationExample() {
  const [storyId, setStoryId] = useState<number | null>(null);

  const generateStory = async (premise: string, genre: string) => {
    // Set context for this operation
    setContext('story_generation', {
      premise,
      genre,
      timestamp: new Date().toISOString(),
    });

    // Add breadcrumb
    addBreadcrumb('Starting story generation', 'story', 'info', {
      premise,
      genre,
    });

    // Set tag for filtering in Sentry
    setTag('operation', 'generate_story');
    setTag('genre', genre);

    try {
      // Track the API call with performance monitoring
      const result = await trackAPICall(
        () => apiCall('POST', '/generate_outline', { premise, genre }),
        '/generate_outline',
        'POST'
      );

      setStoryId(result.story_id);

      addBreadcrumb('Story generated successfully', 'story', 'info', {
        storyId: result.story_id,
      });

      // Set story ID in context
      setTag('story_id', result.story_id.toString());
      setContext('current_story', {
        storyId: result.story_id,
        premise,
        genre,
      });

      return result;
    } catch (error) {
      // Capture error with context
      captureException(error as Error, {
        context: 'story_generation',
        premise,
        genre,
        error_type: 'generation_failed',
      });

      // Show user feedback dialog
      showFeedbackDialog();

      throw error;
    }
  };

  return null; // Example component
}

// Example 3: Tracking beat operations
export function BeatEditorExample() {
  const updateBeat = async (beatId: number, updates: any) => {
    // Add breadcrumb for user action
    addBreadcrumb('User updating beat', 'beat', 'info', {
      beatId,
      fields: Object.keys(updates),
    });

    setTag('operation', 'update_beat');
    setTag('beat_id', beatId.toString());

    try {
      const result = await apiCall('PUT', `/beats/${beatId}`, updates);
      
      addBreadcrumb('Beat updated successfully', 'beat', 'info', {
        beatId,
      });

      return result;
    } catch (error) {
      captureException(error as Error, {
        context: 'beat_update',
        beatId,
        updates,
        error_type: 'update_failed',
      });
      throw error;
    }
  };

  return null; // Example component
}

// Example 4: Tracking page views and navigation
export function NavigationExample() {
  useEffect(() => {
    // Track page view
    addBreadcrumb('Page view', 'navigation', 'info', {
      path: window.location.pathname,
      referrer: document.referrer,
    });

    setTag('page', window.location.pathname);
    setContext('navigation', {
      path: window.location.pathname,
      timestamp: new Date().toISOString(),
    });
  }, []);

  return null; // Example component
}

// Example 5: Monitoring slow operations
export function PerformanceTrackingExample() {
  const processLargeFile = async (file: File) => {
    // Set context
    setContext('file_processing', {
      fileName: file.name,
      fileSize: file.size,
      fileType: file.type,
    });

    addBreadcrumb('Starting file processing', 'file', 'info', {
      fileName: file.name,
      size: file.size,
    });

    const startTime = performance.now();

    try {
      // Your processing logic
      const result = await processFile(file);

      const duration = performance.now() - startTime;

      // Log slow operations
      if (duration > 5000) {
        captureMessage('Slow file processing detected', 'warning', {
          fileName: file.name,
          duration,
          fileSize: file.size,
        });
      }

      addBreadcrumb('File processed successfully', 'file', 'info', {
        fileName: file.name,
        duration,
      });

      return result;
    } catch (error) {
      captureException(error as Error, {
        context: 'file_processing',
        fileName: file.name,
        fileSize: file.size,
        error_type: 'processing_failed',
      });
      throw error;
    }
  };

  return null; // Example component
}

// Helper function (placeholder)
async function processFile(file: File): Promise<any> {
  // Implementation here
  return {};
}

// Example 6: Tracking business logic errors
export function BusinessLogicExample() {
  const validateStoryOutline = (outline: any) => {
    try {
      if (!outline.beats || outline.beats.length === 0) {
        // This is a business logic error, not a technical error
        captureMessage('Story outline validation failed: No beats', 'warning', {
          context: 'validation',
          outlineId: outline.id,
          error_type: 'validation_error',
        });
        return false;
      }

      if (outline.beats.length < 3) {
        captureMessage('Story outline validation failed: Too few beats', 'warning', {
          context: 'validation',
          outlineId: outline.id,
          beatCount: outline.beats.length,
        });
        return false;
      }

      addBreadcrumb('Story outline validated successfully', 'validation', 'info', {
        outlineId: outline.id,
        beatCount: outline.beats.length,
      });

      return true;
    } catch (error) {
      captureException(error as Error, {
        context: 'validation',
        outlineId: outline.id,
      });
      throw error;
    }
  };

  return null; // Example component
}
