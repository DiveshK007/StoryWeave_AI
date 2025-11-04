import React, { useState } from 'react';
import { Sparkles, Loader2, UserPlus } from 'lucide-react';
import { characterApi } from '../lib/characterApi';
import type { CharacterRole, Character } from '../types/character';

interface CharacterCreatorProps {
  storyId: number;
  onCharacterCreated?: (character: Character) => void;
}

export function CharacterCreator({ storyId, onCharacterCreated }: CharacterCreatorProps) {
  const [name, setName] = useState('');
  const [role, setRole] = useState<CharacterRole>('supporting');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!name.trim()) {
      setError('Character name is required');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const character = await characterApi.generateCharacter({
        story_id: storyId,
        name: name.trim(),
        role,
      });

      setName('');
      setRole('supporting');
      onCharacterCreated?.(character);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create character');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center gap-2 mb-4">
        <UserPlus className="w-5 h-5 text-indigo-400" />
        <h3 className="text-lg font-semibold text-white">Create Character</h3>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Character Name
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Enter character name"
            className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-indigo-500 focus:outline-none"
            disabled={loading}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Role
          </label>
          <select
            value={role}
            onChange={(e) => setRole(e.target.value as CharacterRole)}
            className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-indigo-500 focus:outline-none"
            disabled={loading}
          >
            <option value="protagonist">Protagonist</option>
            <option value="antagonist">Antagonist</option>
            <option value="supporting">Supporting</option>
            <option value="minor">Minor</option>
          </select>
        </div>

        {error && (
          <div className="p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-red-400 text-sm">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading || !name.trim()}
          className="w-full px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              Generate Character Profile
            </>
          )}
        </button>
      </form>

      <p className="mt-4 text-xs text-gray-400">
        AI will generate a comprehensive character profile including physical description, personality traits, backstory, goals, motivations, fears, and flaws.
      </p>
    </div>
  );
}
