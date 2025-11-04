import React from 'react';
import { BarChart3, TrendingUp } from 'lucide-react';
import { AdminAnalytics } from '../components/AdminAnalytics';

export function AnalyticsPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-600 flex items-center justify-center">
            <BarChart3 className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white">Analytics</h1>
        </div>
        <p className="text-gray-400">Track your story creation and user engagement metrics</p>
      </div>

      {/* Analytics Dashboard */}
      <div className="bg-gray-800/50 backdrop-blur-lg rounded-2xl border border-gray-700/50 overflow-hidden">
        <div className="p-6 border-b border-gray-700/50">
          <div className="flex items-center gap-3">
            <TrendingUp className="w-5 h-5 text-indigo-400" />
            <h2 className="text-xl font-bold text-white">Key Metrics</h2>
          </div>
        </div>
        <div className="p-6">
          <AdminAnalytics />
        </div>
      </div>
    </div>
  );
}
