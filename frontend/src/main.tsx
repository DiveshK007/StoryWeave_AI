import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import { initSentry } from './lib/sentry';
import { ErrorBoundary } from './components/ErrorBoundary';
import { AnalyticsConsent } from './components/AnalyticsConsent';
import App from './App';

// Initialize Sentry before rendering the app
initSentry();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
      <AnalyticsConsent />
    </ErrorBoundary>
  </React.StrictMode>
);
