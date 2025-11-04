import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  BookOpen, Plus, Search, Filter, Grid, List, 
  Clock, FileText, Loader2, Sparkles
} from 'lucide-react';
import { api } from '../lib/api';
import { StoryCreator } from '../components/StoryCreator';
import { demoStories, shouldUseDemoData } from '../lib/demoData';

interface Story {
  id: number;
  premise: string;
  genre?: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export function StoriesList() {
  const [stories, setStories] = useState<Story[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [creatorOpen, setCreatorOpen] = useState(false);
  const [usingDemo, setUsingDemo] = useState(false);

  useEffect(() => {
    loadStories();
  }, []);

  const loadStories = async () => {
    try {
      setLoading(true);
      const response = await api.get('/stories');
      const storiesData = response.data?.stories || response.data || [];
      setStories(storiesData);
      setUsingDemo(false);
    } catch (error) {
      console.warn('API unavailable, using demo data:', error);
      setStories(demoStories as Story[]);
      setUsingDemo(true);
    } finally {
      setLoading(false);
    }
  };

  const filteredStories = stories.filter(story =>
    story.premise?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    story.genre?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      draft: 'bg-bg-tertiary text-text-secondary border-border-subtle',
      outline: 'bg-info/20 text-info border-info/30',
      in_progress: 'bg-warning/20 text-warning border-warning/30',
      completed: 'bg-success/20 text-success border-success/30',
    };
    return colors[status] || colors.draft;
  };

  const handleStoryCreated = (storyId: number) => {
    loadStories();
    // Optionally navigate to the new story
    window.location.href = `/stories/${storyId}`;
  };

  return (
    <>
      <div className="space-y-6">
        {usingDemo && (
          <div className="bg-warning/20 border border-warning/30 rounded-lg p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-warning/30 flex items-center justify-center flex-shrink-0">
              <Sparkles className="w-5 h-5 text-warning" />
            </div>
            <div>
              <p className="text-sm font-medium text-text-primary">Demo Mode</p>
              <p className="text-xs text-text-secondary">Showing sample stories. Create a story to test the full functionality.</p>
            </div>
          </div>
        )}

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-text-primary mb-2">Your Projects</h1>
            <p className="text-text-secondary">Manage and organize all your stories</p>
          </div>
          <button
            onClick={() => setCreatorOpen(true)}
            className="btn-primary inline-flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            <span>New Story</span>
          </button>
        </div>

        {/* Search and Filters */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-text-tertiary" />
            <input
              type="text"
              placeholder="Search projects..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="form-input pl-12"
            />
          </div>
          <div className="flex items-center gap-2">
            <button className="btn-icon">
              <Filter className="w-5 h-5" />
            </button>
            <div className="flex items-center bg-bg-tertiary border border-border-subtle rounded-lg p-1">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 rounded-lg transition-colors ${
                  viewMode === 'grid'
                    ? 'bg-primary-500 text-white'
                    : 'text-text-secondary hover:text-text-primary'
                }`}
              >
                <Grid className="w-5 h-5" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 rounded-lg transition-colors ${
                  viewMode === 'list'
                    ? 'bg-primary-500 text-white'
                    : 'text-text-secondary hover:text-text-primary'
                }`}
              >
                <List className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Stories */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
          </div>
        ) : filteredStories.length === 0 ? (
          <div className="text-center py-20">
            <div className="w-20 h-20 rounded-full bg-bg-tertiary mx-auto mb-6 flex items-center justify-center">
              <BookOpen className="w-10 h-10 text-text-tertiary" />
            </div>
            <h3 className="text-xl font-semibold text-text-primary mb-2">
              {searchQuery ? 'No projects found' : 'No projects yet'}
            </h3>
            <p className="text-text-secondary mb-6">
              {searchQuery
                ? 'Try adjusting your search query'
                : 'Create your first story to get started!'}
            </p>
            {!searchQuery && (
              <button
                onClick={() => setCreatorOpen(true)}
                className="btn-primary inline-flex items-center gap-2"
              >
                <Sparkles className="w-5 h-5" />
                <span>Create Story</span>
              </button>
            )}
          </div>
        ) : viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredStories.map((story) => (
              <Link
                key={story.id}
                to={`/stories/${story.id}`}
                className="card card-hover group"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 rounded-xl bg-gradient-brand flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
                    <BookOpen className="w-6 h-6 text-white" />
                  </div>
                  <span className={`px-2 py-1 text-xs rounded-full border ${getStatusColor(story.status)}`}>
                    {story.status || 'draft'}
                  </span>
                </div>
                <h3 className="text-lg font-semibold text-text-primary mb-2 line-clamp-2 group-hover:text-primary-400 transition-colors">
                  {story.premise || `Story #${story.id}`}
                </h3>
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
              </Link>
            ))}
          </div>
        ) : (
          <div className="card divide-y divide-border-subtle">
            {filteredStories.map((story) => (
              <Link
                key={story.id}
                to={`/stories/${story.id}`}
                className="block p-6 hover:bg-bg-hover transition-colors group"
              >
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-4 flex-1 min-w-0">
                    <div className="w-12 h-12 rounded-xl bg-gradient-brand flex items-center justify-center shadow-lg flex-shrink-0">
                      <BookOpen className="w-6 h-6 text-white" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-1">
                        <h3 className="text-lg font-semibold text-text-primary group-hover:text-primary-400 transition-colors truncate">
                          {story.premise || `Story #${story.id}`}
                        </h3>
                        <span className={`px-2 py-1 text-xs rounded-full border ${getStatusColor(story.status)}`}>
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
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      <StoryCreator
        isOpen={creatorOpen}
        onClose={() => setCreatorOpen(false)}
        onSuccess={handleStoryCreated}
      />
    </>
  );
}
