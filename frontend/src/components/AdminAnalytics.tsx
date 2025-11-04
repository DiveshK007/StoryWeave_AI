import React, { useState, useEffect } from 'react';
import { BarChart3, Users, BookOpen, Clock, TrendingUp, AlertCircle } from 'lucide-react';
import { api } from '../lib/api';

interface AnalyticsData {
  period: {
    start: string;
    end: string;
    days: number;
  };
  dau?: {
    total: number;
    daily: any[];
  };
  stories?: {
    total: any;
    daily: any[];
  };
  generation_time?: {
    average: number;
    trend: any[];
  };
  genres?: Array<{ genre: string; count: number }>;
  funnel?: Array<{
    step: string;
    count: number;
    conversion_rate: number | null;
  }>;
  new_users?: {
    total: number;
    daily: any[];
  };
  active_users?: {
    total: number;
    daily: any[];
  };
  errors?: Array<{ error_type: string; count: number }>;
  total?: number;
}

export function AdminAnalytics() {
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState<AnalyticsData | null>(null);
  const [genres, setGenres] = useState<AnalyticsData | null>(null);
  const [funnel, setFunnel] = useState<AnalyticsData | null>(null);
  const [users, setUsers] = useState<AnalyticsData | null>(null);
  const [errors, setErrors] = useState<AnalyticsData | null>(null);
  const [days, setDays] = useState(7);

  useEffect(() => {
    loadAnalytics();
  }, [days]);

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const [overviewData, genresData, funnelData, usersData, errorsData] = await Promise.all([
        api.get(`/admin/analytics/overview?days=${days}`),
        api.get(`/admin/analytics/genres?days=${days}`),
        api.get('/admin/analytics/funnel'),
        api.get(`/admin/analytics/users?days=${days}`),
        api.get(`/admin/analytics/errors?days=${days}`),
      ]);

      setOverview(overviewData.data);
      setGenres(genresData.data);
      setFunnel(funnelData.data);
      setUsers(usersData.data);
      setErrors(errorsData.data);
    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Analytics Dashboard</h1>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="px-4 py-2 bg-gray-700 text-white rounded-lg border border-gray-600"
        >
          <option value={1}>Last 24 hours</option>
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Daily Active Users"
          value={overview?.dau?.total || users?.active_users?.total || 0}
          icon={Users}
          trend={users?.active_users?.daily?.length}
        />
        <MetricCard
          title="Stories Created"
          value={Object.values(overview?.stories?.total || {}).reduce((a: number, b: any) => a + (b || 0), 0)}
          icon={BookOpen}
        />
        <MetricCard
          title="Avg Generation Time"
          value={`${((overview?.generation_time?.average || 0) / 1000).toFixed(1)}s`}
          icon={Clock}
        />
        <MetricCard
          title="Error Rate"
          value={errors?.total || 0}
          icon={AlertCircle}
          variant="error"
        />
      </div>

      {/* Genres */}
      {genres && genres.genres && (
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold text-white mb-4">Most Popular Genres</h2>
          <div className="space-y-2">
            {genres.genres.map((item, index) => (
              <div key={item.genre} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-gray-400 w-8">{index + 1}.</span>
                  <span className="text-white">{item.genre}</span>
                </div>
                <span className="text-indigo-400 font-medium">{item.count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Funnel */}
      {funnel && funnel.funnel && (
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold text-white mb-4">Feature Usage Funnel</h2>
          <div className="space-y-4">
            {funnel.funnel.map((step, index) => (
              <div key={step.step} className="relative">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-white capitalize">{step.step.replace(/_/g, ' ')}</span>
                  <div className="flex items-center gap-4">
                    <span className="text-indigo-400 font-medium">{step.count}</span>
                    {step.conversion_rate !== null && (
                      <span className="text-gray-400 text-sm">
                        {step.conversion_rate.toFixed(1)}%
                      </span>
                    )}
                  </div>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-indigo-600 h-2 rounded-full transition-all"
                    style={{
                      width: `${(step.count / (funnel.funnel?.[0]?.count || 1)) * 100}%`
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Errors */}
      {errors && errors.errors && errors.errors.length > 0 && (
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold text-white mb-4">Error Breakdown</h2>
          <div className="space-y-2">
            {errors.errors.map((error) => (
              <div key={error.error_type} className="flex items-center justify-between">
                <span className="text-white capitalize">{error.error_type.replace(/_/g, ' ')}</span>
                <span className="text-red-400 font-medium">{error.count}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  trend?: any;
  variant?: 'default' | 'error';
}

function MetricCard({ title, value, icon: Icon, trend, variant = 'default' }: MetricCardProps) {
  const colorClass = variant === 'error' ? 'text-red-400' : 'text-indigo-400';
  
  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-gray-400 text-sm font-medium">{title}</h3>
        <Icon className={`w-5 h-5 ${colorClass}`} />
      </div>
      <p className={`text-2xl font-bold ${variant === 'error' ? 'text-red-400' : 'text-white'}`}>
        {value}
      </p>
      {trend && (
        <p className="text-xs text-gray-500 mt-1">
          {Array.isArray(trend) ? `${trend.length} data points` : ''}
        </p>
      )}
    </div>
  );
}
