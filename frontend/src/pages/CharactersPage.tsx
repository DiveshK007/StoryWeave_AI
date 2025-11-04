import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Plus, Users, Sparkles } from 'lucide-react';
import { CharacterList } from '../components/CharacterList';
import { CharacterCreator } from '../components/CharacterCreator';
import { getDemoCharacters } from '../lib/demoData';

export function CharactersPage() {
  const { storyId } = useParams<{ storyId: string }>();
  const [showCreator, setShowCreator] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const [usingDemo, setUsingDemo] = useState(false);

  useEffect(() => {
    // Check if we should use demo data (for story ID 1)
    if (storyId === '1') {
      const demoChars = getDemoCharacters(1);
      if (demoChars.length > 0) {
        setUsingDemo(true);
      }
    }
  }, [storyId]);

  const handleCharacterCreated = () => {
    setShowCreator(false);
    setRefreshKey(prev => prev + 1);
  };

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            to={`/stories/${storyId}`}
            className="btn-icon"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-text-primary mb-2">Characters</h1>
            <p className="text-text-secondary">Manage your story's characters</p>
          </div>
        </div>
        <button
          onClick={() => setShowCreator(true)}
          className="btn-primary inline-flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          <span>New Character</span>
        </button>
      </div>

      {/* Character Creator Modal */}
      {showCreator && storyId && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-bg-secondary border border-border-default rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto animate-slide-up shadow-2xl">
            <div className="p-6 border-b border-border-subtle flex items-center justify-between">
              <h2 className="text-xl font-bold text-text-primary">Create New Character</h2>
              <button
                onClick={() => setShowCreator(false)}
                className="btn-icon"
              >
                ✕
              </button>
            </div>
            <div className="p-6">
              <CharacterCreator
                storyId={Number(storyId)}
                onSuccess={handleCharacterCreated}
                onCancel={() => setShowCreator(false)}
              />
            </div>
          </div>
        </div>
      )}

      {/* Character List */}
      {storyId && (
        <div className="card">
          <div className="mb-6 pb-4 border-b border-border-subtle">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-creative flex items-center justify-center">
                <Users className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-text-primary">Story Characters</h2>
                <p className="text-sm text-text-secondary">All characters in this story</p>
              </div>
            </div>
          </div>
          <CharacterList key={refreshKey} storyId={Number(storyId)} />
        </div>
      )}
    </div>
  );
}
