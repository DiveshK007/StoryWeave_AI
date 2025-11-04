import React, { useState, useEffect } from 'react';
import { X, Shield, BarChart3 } from 'lucide-react';
import { initMixpanel, setAnalyticsEnabled } from '../lib/analytics';

interface AnalyticsConsentProps {
  onConsentChange?: (consented: boolean) => void;
}

/**
 * GDPR-compliant analytics consent banner.
 * Shows on first visit and allows users to opt-in/opt-out.
 */
export function AnalyticsConsent({ onConsentChange }: AnalyticsConsentProps) {
  const [showBanner, setShowBanner] = useState(false);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Check if user has already made a choice
    const consent = localStorage.getItem('analytics_consent');
    const dismissed = localStorage.getItem('analytics_banner_dismissed');

    if (!consent && !dismissed) {
      // Show banner after a short delay
      setTimeout(() => {
        setShowBanner(true);
        setTimeout(() => setIsVisible(true), 100);
      }, 1000);
    } else if (consent === 'true') {
      // User previously consented, initialize
      initMixpanel();
      setAnalyticsEnabled(true);
    }
  }, []);

  const handleAccept = () => {
    localStorage.setItem('analytics_consent', 'true');
    localStorage.setItem('analytics_banner_dismissed', 'true');
    setShowBanner(false);
    setIsVisible(false);
    
    // Initialize analytics
    initMixpanel();
    setAnalyticsEnabled(true);
    
    onConsentChange?.(true);
  };

  const handleDecline = () => {
    localStorage.setItem('analytics_consent', 'false');
    localStorage.setItem('analytics_banner_dismissed', 'true');
    setShowBanner(false);
    setIsVisible(false);
    
    // Disable analytics
    setAnalyticsEnabled(false);
    
    onConsentChange?.(false);
  };

  const handleDismiss = () => {
    localStorage.setItem('analytics_banner_dismissed', 'true');
    setShowBanner(false);
    setIsVisible(false);
  };

  if (!showBanner) {
    return null;
  }

  return (
    <div
      className={`fixed bottom-0 left-0 right-0 z-50 transition-all duration-300 ${
        isVisible ? 'translate-y-0 opacity-100' : 'translate-y-full opacity-0'
      }`}
    >
      <div className="max-w-7xl mx-auto p-4">
        <div className="bg-gray-800 border border-gray-700 rounded-lg shadow-xl p-6 relative">
          <button
            onClick={handleDismiss}
            className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
            aria-label="Dismiss"
          >
            <X className="w-5 h-5" />
          </button>

          <div className="flex items-start gap-4">
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-indigo-500/20 rounded-lg flex items-center justify-center">
                <Shield className="w-6 h-6 text-indigo-400" />
              </div>
            </div>

            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <BarChart3 className="w-5 h-5 text-indigo-400" />
                <h3 className="text-lg font-semibold text-white">
                  We value your privacy
                </h3>
              </div>

              <p className="text-gray-300 mb-4 text-sm">
                We use analytics to improve your experience. We track page views, 
                feature usage, and errors to make StoryWeave AI better. All data 
                is anonymized and stored securely. You can opt out at any time.
              </p>

              <div className="flex flex-wrap gap-3">
                <button
                  onClick={handleAccept}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors font-medium"
                >
                  Accept Analytics
                </button>
                <button
                  onClick={handleDecline}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors font-medium"
                >
                  Decline
                </button>
                <button
                  onClick={handleDismiss}
                  className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                >
                  Maybe Later
                </button>
              </div>

              <p className="text-xs text-gray-500 mt-3">
                Read our{' '}
                <a
                  href="/privacy"
                  className="text-indigo-400 hover:text-indigo-300 underline"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Privacy Policy
                </a>
                {' '}for more information. Data retention: 90 days.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
