import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  BookOpen, Plus, TrendingUp, Clock, Sparkles, 
  Users, FileText, ArrowRight, Loader2, Upload
} from 'lucide-react';
import { api } from '../lib/api';
import { demoStories, demoStats, shouldUseDemoData } from '../lib/demoData';

interface Story {
  id: number;
  premise: string;
  genre?: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export function Dashboard() {
  const [stories, setStories] = useState<Story[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalStories: 0,
    activeStories: 0,
    totalCharacters: 0,
  });
  const [usingDemo, setUsingDemo] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const response = await api.get('/stories?limit=5');
      const storiesData = response.data?.stories || response.data || [];
      setStories(storiesData);
      setStats({
        totalStories: storiesData.length,
        activeStories: storiesData.filter((s: Story) => s.status !== 'completed').length,
        totalCharacters: 0,
      });
      setUsingDemo(false);
    } catch (error) {
      console.warn('API unavailable, using demo data:', error);
      // Use demo data on error
      const demoData = demoStories.slice(0, 5);
      setStories(demoData as Story[]);
      setStats({
        totalStories: demoStats.totalStories,
        activeStories: demoStats.activeStories,
        totalCharacters: demoStats.totalCharacters,
      });
      setUsingDemo(true);
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({ 
    icon: Icon, 
    title, 
    value, 
    change, 
    gradient 
  }: { 
    icon: any; 
    title: string; 
    value: string | number; 
    change?: string; 
    gradient: string;
  }) => (
    <div className="card card-hover group">
      <div className="flex items-center justify-between mb-4">
        <div className={`w-12 h-12 rounded-xl ${gradient} flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        {change && (
          <span className="text-xs px-2 py-1 rounded-full bg-success/20 text-success border border-success/30">
            {change}
          </span>
        )}
      </div>
      <h3 className="text-2xl font-bold text-text-primary mb-1">{value}</h3>
      <p className="text-sm text-text-secondary">{title}</p>
    </div>
  );

  const userName = localStorage.getItem('user_email')?.split('@')[0] || 'Creator';

  return (
    <div className="space-y-8">
      {usingDemo && (
        <div className="bg-warning/20 border border-warning/30 rounded-lg p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-warning/30 flex items-center justify-center flex-shrink-0">
            <Sparkles className="w-5 h-5 text-warning" />
          </div>
          <div>
            <p className="text-sm font-medium text-text-primary">Demo Mode</p>
            <p className="text-xs text-text-secondary">Showing sample data. Connect to the backend API to see your stories.</p>
          </div>
        </div>
      )}

      {/* Hero Section */}
      <div className="relative overflow-hidden bg-gradient-mesh rounded-2xl p-12 text-center border border-border-subtle">
        <div className="relative z-10">
          <h1 className="text-4xl md:text-5xl font-bold mb-3 gradient-text-white">
            Welcome back, {userName}! 👋
          </h1>
          <p className="text-lg text-text-secondary mb-8 max-w-2xl mx-auto">
            Create your next masterpiece with AI-powered story generation
          </p>
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <Link
              to="/stories"
              className="btn-primary btn-lg inline-flex items-center gap-2"
            >
              <Plus className="w-5 h-5" />
              <span>New Story</span>
            </Link>
            <button className="btn-secondary btn-lg inline-flex items-center gap-2">
              <Upload className="w-5 h-5" />
              <span>Upload Corpus</span>
            </button>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard
          icon={BookOpen}
          title="Total Stories"
          value={stats.totalStories}
          gradient="bg-gradient-primary"
        />
        <StatCard
          icon={TrendingUp}
          title="Active Stories"
          value={stats.activeStories}
          change="+2 this week"
          gradient="bg-gradient-creative"
        />
        <StatCard
          icon={Users}
          title="Characters Created"
          value={stats.totalCharacters}
          gradient="bg-gradient-success"
        />
      </div>

      {/* Recent Stories */}
      <div className="card">
        <div className="flex items-center justify-between mb-6 pb-4 border-b border-border-subtle">
          <div>
            <h2 className="text-2xl font-bold text-text-primary mb-1">Recent Projects</h2>
            <p className="text-sm text-text-secondary">Continue where you left off</p>
          </div>
          <Link
            to="/stories"
            className="text-sm text-primary-500 hover:text-primary-400 flex items-center gap-1 font-medium transition-colors"
          >
            View all <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {loading ? (
          <div className="py-12 flex items-center justify-center">
            <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
          </div>
        ) : stories.length === 0 ? (
          <div className="py-12 text-center">
            <div className="w-16 h-16 rounded-full bg-bg-tertiary mx-auto mb-4 flex items-center justify-center">
              <BookOpen className="w-8 h-8 text-text-tertiary" />
            </div>
            <h3 className="text-lg font-semibold text-text-primary mb-2">No stories yet</h3>
            <p className="text-text-secondary mb-6">Create your first story to get started!</p>
            <Link
              to="/stories"
              className="btn-primary inline-flex items-center gap-2"
            >
              <Sparkles className="w-5 h-5" />
              <span>Create Story</span>
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {stories.map((story) => (
              <Link
                key={story.id}
                to={`/stories/${story.id}`}
                className="block p-4 rounded-lg bg-bg-tertiary border border-border-subtle hover:border-primary-500 hover:bg-bg-hover transition-all group"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-text-primary group-hover:text-primary-400 transition-colors truncate">
                        {story.premise || `Story #${story.id}`}
                      </h3>
                      <span className="px-2 py-1 text-xs rounded-full bg-primary-500/20 text-primary-400 border border-primary-500/30">
                        {story.status || 'draft'}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-text-secondary">
                      {story.genre && (
                        <span className="flex items-center gap-1">
                          <FileText className="w-4 h-4" />
                          {story.genre}
                        </span>
                      )}
                      <span className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {new Date(story.updated_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                  <ArrowRight className="w-5 h-5 text-text-tertiary group-hover:text-primary-400 transition-colors flex-shrink-0" />
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card bg-gradient-to-br from-primary-500/10 to-accent-500/10 border-primary-500/20">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-gradient-brand flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <h3 className="text-lg font-semibold text-text-primary">AI Story Generator</h3>
          </div>
          <p className="text-text-secondary mb-4">
            Let AI help you craft compelling stories with intelligent outline generation and scene expansion.
          </p>
          <Link
            to="/stories"
            className="inline-flex items-center gap-2 text-primary-500 hover:text-primary-400 font-medium transition-colors"
          >
            Try it now <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        <div className="card bg-gradient-to-br from-accent-500/10 to-primary-500/10 border-accent-500/20">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-gradient-creative flex items-center justify-center">
              <Users className="w-5 h-5 text-white" />
            </div>
            <h3 className="text-lg font-semibold text-text-primary">Character Development</h3>
          </div>
          <p className="text-text-secondary mb-4">
            Create rich, consistent characters with AI-powered profiles and relationship tracking.
          </p>
          <Link
            to="/stories/1/characters"
            className="inline-flex items-center gap-2 text-accent-500 hover:text-accent-400 font-medium transition-colors"
          >
            Explore <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}
