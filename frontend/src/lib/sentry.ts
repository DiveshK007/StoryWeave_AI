/**
 * Sentry configuration and utilities for frontend error tracking and monitoring.
 */
import * as Sentry from '@sentry/react';

let isInitialized = false;

export function initSentry(dsn?: string, environment?: string, release?: string) {
  if (isInitialized) {
    console.warn('Sentry already initialized');
    return;
  }

  dsn = dsn || import.meta.env.VITE_SENTRY_DSN;
  environment = environment || import.meta.env.MODE || 'development';

  if (!dsn) {
    console.warn('Sentry DSN not provided. Error tracking disabled.');
    return;
  }

  Sentry.init({
    dsn,
    environment,
    release: release || import.meta.env.VITE_SENTRY_RELEASE || '1.0.0',
    integrations: [
      Sentry.browserTracingIntegration({
        // Set sampling rate for performance monitoring
        tracePropagationTargets: ['localhost', /^\//],
      }),
      Sentry.browserProfilingIntegration(),
      Sentry.replayIntegration({
        // Session Replay
        maskAllText: false,
        blockAllMedia: false,
      }),
      Sentry.feedbackIntegration({
        // User feedback widget
        colorScheme: 'dark',
        showBranding: false,
        isNameRequired: false,
        isEmailRequired: false,
      }),
    ],
    // Performance Monitoring
    tracesSampleRate: environment === 'production' ? 0.1 : 1.0,
    profilesSampleRate: environment === 'production' ? 0.1 : 1.0,
    
    // Session Replay
    replaysSessionSampleRate: environment === 'production' ? 0.1 : 1.0,
    replaysOnErrorSampleRate: 1.0,
    
    // Filter sensitive data
    beforeSend(event, hint) {
      // Filter sensitive data from breadcrumbs
      if (event.breadcrumbs) {
        event.breadcrumbs = event.breadcrumbs.map((crumb) => {
          if (crumb.data) {
            // Remove sensitive fields
            const sensitiveKeys = ['password', 'token', 'api_key', 'secret', 'authorization'];
            const filteredData: Record<string, any> = {};
            
            for (const [key, value] of Object.entries(crumb.data)) {
              if (!sensitiveKeys.some((sensitive) => key.toLowerCase().includes(sensitive))) {
                filteredData[key] = value;
              } else {
                filteredData[key] = '[FILTERED]';
              }
            }
            
            crumb.data = filteredData;
          }
          return crumb;
        });
      }
      
      // Filter sensitive data from request
      if (event.request) {
        if (event.request.headers) {
          const sensitiveHeaders = ['authorization', 'cookie', 'x-api-key'];
          for (const header of sensitiveHeaders) {
            delete event.request.headers[header];
            delete event.request.headers[header.toLowerCase()];
            delete event.request.headers[header.toUpperCase()];
          }
        }
        
        if (event.request.query_string) {
          const queryParams = new URLSearchParams(event.request.query_string);
          const sensitiveParams = ['password', 'token', 'api_key', 'secret', 'authorization'];
          sensitiveParams.forEach((param) => {
            queryParams.delete(param);
            queryParams.delete(param.toLowerCase());
          });
          event.request.query_string = queryParams.toString();
        }
      }
      
      return event;
    },
    
    // Ignore certain errors
    ignoreErrors: [
      // Browser extensions
      'top.GLOBALS',
      'originalCreateNotification',
      'canvas.contentDocument',
      'MyApp_RemoveAllHighlights',
      'atomicFindClose',
      // Network errors
      'Network request failed',
      'Failed to fetch',
      'NetworkError',
      // Chrome extensions
      'chrome-extension://',
    ],
    
    // Don't send PII by default
    sendDefaultPii: false,
  });

  isInitialized = true;
  console.log(`Sentry initialized for environment: ${environment}`);
}

/**
 * Set user context in Sentry.
 */
export function setUserContext(userId?: string | number, email?: string, username?: string) {
  Sentry.setUser({
    id: userId ? String(userId) : undefined,
    email,
    username,
  });
}

/**
 * Clear user context (e.g., on logout).
 */
export function clearUserContext() {
  Sentry.setUser(null);
}

/**
 * Set additional context for the current scope.
 */
export function setContext(key: string, context: Record<string, any>) {
  Sentry.setContext(key, context);
}

/**
 * Add a breadcrumb for debugging.
 */
export function addBreadcrumb(
  message: string,
  category: string = 'default',
  level: Sentry.SeverityLevel = 'info',
  data?: Record<string, any>
) {
  Sentry.addBreadcrumb({
    message,
    category,
    level,
    data,
  });
}

/**
 * Set a tag for error grouping and filtering.
 */
export function setTag(key: string, value: string) {
  Sentry.setTag(key, value);
}

/**
 * Capture an exception manually.
 */
export function captureException(error: Error, context?: Record<string, any>) {
  if (context) {
    Sentry.withScope((scope) => {
      Object.entries(context).forEach(([key, value]) => {
        scope.setExtra(key, value);
      });
      Sentry.captureException(error);
    });
  } else {
    Sentry.captureException(error);
  }
}

/**
 * Capture a message manually.
 */
export function captureMessage(message: string, level: Sentry.SeverityLevel = 'info', context?: Record<string, any>) {
  if (context) {
    Sentry.withScope((scope) => {
      Object.entries(context).forEach(([key, value]) => {
        scope.setExtra(key, value);
      });
      Sentry.captureMessage(message, level);
    });
  } else {
    Sentry.captureMessage(message, level);
  }
}

/**
 * Track performance transaction.
 */
export function startTransaction(name: string, op: string = 'navigation') {
  return Sentry.startSpan({ name, op }, () => {
    // Span will be automatically finished when callback completes
    return {};
  });
}

/**
 * Track API call with Sentry.
 */
export async function trackAPICall<T>(
  apiCall: () => Promise<T>,
  endpoint: string,
  method: string = 'GET'
): Promise<T> {
  return Sentry.startSpan(
    {
      name: `API ${method} ${endpoint}`,
      op: 'http.client',
      attributes: {
        'http.method': method,
        'http.url': endpoint,
      },
    },
    async () => {
      addBreadcrumb(`API Call: ${method} ${endpoint}`, 'api', 'info', {
        method,
        endpoint,
      });

      try {
        const result = await apiCall();
        return result;
      } catch (error) {
        captureException(error as Error, {
          endpoint,
          method,
          error_type: 'api_error',
        });
        throw error;
      }
    }
  );
}

/**
 * Show user feedback dialog on error.
 */
export function showFeedbackDialog() {
  Sentry.showReportDialog();
}
