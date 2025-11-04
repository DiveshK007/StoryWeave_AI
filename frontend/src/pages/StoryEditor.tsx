import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, Users, Save, Loader2, Sparkles, 
  Download, Share2, Edit2, Check, X
} from 'lucide-react';
import { BeatEditor } from '../components/BeatEditor';
import { api } from '../lib/api';
import { getDemoStory, getDemoBeats, shouldUseDemoData } from '../lib/demoData';

export function StoryEditor() {
  const { storyId } = useParams<{ storyId: string }>();
  const navigate = useNavigate();
  const [story, setStory] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editingPremise, setEditingPremise] = useState(false);
  const [editingLogline, setEditingLogline] = useState(false);
  const [premiseText, setPremiseText] = useState('');
  const [loglineText, setLoglineText] = useState('');
  const [usingDemo, setUsingDemo] = useState(false);

  useEffect(() => {
    if (storyId) {
      loadStory();
    }
  }, [storyId]);

  const loadStory = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/stories/${storyId}`);
      const storyData = response.data;
      setStory(storyData);
      setPremiseText(storyData.premise || '');
      setLoglineText(storyData.logline || '');
      setUsingDemo(false);
    } catch (error) {
      console.warn('API unavailable, using demo data:', error);
      // Use demo data
      const demoStory = getDemoStory(Number(storyId));
      if (demoStory) {
        setStory(demoStory);
        setPremiseText(demoStory.premise || '');
        setLoglineText(demoStory.logline || '');
        setUsingDemo(true);
      } else {
        // Story not found in demo data either
        setStory(null);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSaveStory = async () => {
    if (!story || usingDemo) {
      // In demo mode, just update local state
      setStory({
        ...story,
        premise: premiseText,
        logline: loglineText,
      });
      setEditingPremise(false);
      setEditingLogline(false);
      alert('Demo mode: Changes saved locally. Connect to API to persist.');
      return;
    }
    
    setSaving(true);
    try {
      await api.put(`/stories/${storyId}`, {
        premise: premiseText,
        logline: loglineText,
      });
      await loadStory();
      setEditingPremise(false);
      setEditingLogline(false);
    } catch (error) {
      console.error('Failed to save story:', error);
      alert('Failed to save story. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleExport = async (format: 'pdf' | 'docx' | 'txt') => {
    if (usingDemo) {
      alert('Demo mode: Export functionality requires API connection.');
      return;
    }

    try {
      const response = await api.get(`/stories/${storyId}/export?format=${format}`, {
        responseType: 'blob',
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `story-${storyId}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Failed to export story:', error);
      alert('Failed to export story. Please try again.');
    }
  };

  const handleShare = async () => {
    try {
      const shareUrl = `${window.location.origin}/stories/${storyId}`;
      
      if (navigator.share) {
        await navigator.share({
          title: story?.premise || 'Story',
          text: story?.logline || 'Check out this story!',
          url: shareUrl,
        });
      } else {
        // Fallback: copy to clipboard
        await navigator.clipboard.writeText(shareUrl);
        alert('Story link copied to clipboard!');
      }
    } catch (error) {
      console.error('Failed to share story:', error);
    }
  };

  const handleExpandScene = async (beatId: number) => {
    if (usingDemo) {
      alert('Demo mode: Scene expansion requires API connection.');
      return;
    }

    try {
      const response = await api.post(`/beats/${beatId}/expand`);
      await loadStory();
    } catch (error) {
      console.error('Failed to expand scene:', error);
      alert('Failed to expand scene. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
      </div>
    );
  }

  if (!story) {
    return (
      <div className="text-center py-20">
        <h2 className="text-2xl font-bold text-text-primary mb-2">Story not found</h2>
        <p className="text-text-secondary mb-6">The story you're looking for doesn't exist.</p>
        <Link
          to="/stories"
          className="btn-primary inline-flex items-center gap-2"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>Back to Stories</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            to="/stories"
            className="btn-icon"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-text-primary mb-1">
              {story.premise || `Story #${story.id}`}
            </h1>
            <div className="flex items-center gap-3 text-sm text-text-secondary">
              {story.genre && (
                <span className="px-2 py-1 rounded-full bg-primary-500/20 text-primary-400 border border-primary-500/30">
                  {story.genre}
                </span>
              )}
              <span className="px-2 py-1 rounded-full bg-bg-tertiary text-text-tertiary border border-border-subtle">
                {story.status || 'draft'}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleSaveStory}
            disabled={saving}
            className="btn-primary btn-sm inline-flex items-center gap-2"
          >
            <Save className="w-4 h-4" />
            <span>{saving ? 'Saving...' : 'Save'}</span>
          </button>

          <div className="relative group">
            <button className="btn-secondary btn-sm inline-flex items-center gap-2">
              <Download className="w-4 h-4" />
              <span>Export</span>
            </button>
            <div className="absolute right-0 top-full mt-2 w-32 bg-bg-secondary border border-border-default rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
              <button
                onClick={() => handleExport('pdf')}
                className="w-full px-4 py-2 text-left text-sm text-text-primary hover:bg-bg-hover first:rounded-t-lg last:rounded-b-lg transition-colors"
              >
                Export as PDF
              </button>
              <button
                onClick={() => handleExport('docx')}
                className="w-full px-4 py-2 text-left text-sm text-text-primary hover:bg-bg-hover transition-colors"
              >
                Export as DOCX
              </button>
              <button
                onClick={() => handleExport('txt')}
                className="w-full px-4 py-2 text-left text-sm text-text-primary hover:bg-bg-hover transition-colors"
              >
                Export as TXT
              </button>
            </div>
          </div>

          <button
            onClick={handleShare}
            className="btn-secondary btn-sm inline-flex items-center gap-2"
          >
            <Share2 className="w-4 h-4" />
            <span>Share</span>
          </button>

          <Link
            to={`/stories/${storyId}/characters`}
            className="btn-secondary btn-sm inline-flex items-center gap-2"
          >
            <Users className="w-4 h-4" />
            <span>Characters</span>
          </Link>
        </div>
      </div>

      {/* Story Content */}
      <div className="card">
        {/* Premise Section */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-xl font-semibold text-text-primary">Story Premise</h2>
            {!editingPremise ? (
              <button
                onClick={() => setEditingPremise(true)}
                className="btn-icon btn-sm"
              >
                <Edit2 className="w-4 h-4" />
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    handleSaveStory();
                    setEditingPremise(false);
                  }}
                  className="btn-icon btn-sm"
                  title="Save"
                >
                  <Check className="w-4 h-4 text-success" />
                </button>
                <button
                  onClick={() => {
                    setPremiseText(story.premise || '');
                    setEditingPremise(false);
                  }}
                  className="btn-icon btn-sm"
                  title="Cancel"
                >
                  <X className="w-4 h-4 text-error" />
                </button>
              </div>
            )}
          </div>
          {editingPremise ? (
            <textarea
              className="form-textarea"
              value={premiseText}
              onChange={(e) => setPremiseText(e.target.value)}
              rows={3}
              placeholder="Enter your story premise..."
            />
          ) : (
            <p className="text-text-primary leading-relaxed">
              {story.premise || 'No premise set yet. Click edit to add one.'}
            </p>
          )}
        </div>

        {/* Logline Section */}
        {story.logline || editingLogline ? (
          <div className="p-4 bg-primary-500/10 border border-primary-500/20 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-primary-400">Logline</h3>
              {!editingLogline ? (
                <button
                  onClick={() => setEditingLogline(true)}
                  className="btn-icon btn-sm"
                >
                  <Edit2 className="w-4 h-4" />
                </button>
              ) : (
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      handleSaveStory();
                      setEditingLogline(false);
                    }}
                    className="btn-icon btn-sm"
                    title="Save"
                  >
                    <Check className="w-4 h-4 text-success" />
                  </button>
                  <button
                    onClick={() => {
                      setLoglineText(story.logline || '');
                      setEditingLogline(false);
                    }}
                    className="btn-icon btn-sm"
                    title="Cancel"
                  >
                    <X className="w-4 h-4 text-error" />
                  </button>
                </div>
              )}
            </div>
            {editingLogline ? (
              <textarea
                className="form-input"
                value={loglineText}
                onChange={(e) => setLoglineText(e.target.value)}
                rows={2}
                placeholder="Enter your logline..."
              />
            ) : (
              <p className="text-text-primary">{story.logline}</p>
            )}
          </div>
        ) : (
          <button
            onClick={() => setEditingLogline(true)}
            className="text-sm text-primary-400 hover:text-primary-300 transition-colors"
          >
            + Add logline
          </button>
        )}
      </div>

      {/* Beat Editor */}
      <div className="card">
        <div className="mb-6 pb-4 border-b border-border-subtle">
          <div>
            <h2 className="text-xl font-bold text-text-primary mb-1">Story Beats</h2>
            <p className="text-sm text-text-secondary">Organize your story structure</p>
          </div>
        </div>
        <BeatEditor
          storyId={Number(storyId)}
          onExpandScene={handleExpandScene}
        />
      </div>
    </div>
  );
}
