import React, { useState } from 'react';
import { User, Trash2, CheckCircle, AlertCircle, TrendingUp } from 'lucide-react';
import { characterApi } from '../lib/characterApi';
import type { Character } from '../types/character';

interface CharacterCardProps {
  character: Character;
  onClick?: () => void;
  onDelete?: () => void;
  showActions?: boolean;
}

const roleColors: Record<string, string> = {
  protagonist: 'bg-blue-500/20 text-blue-400 border-blue-500/50',
  antagonist: 'bg-red-500/20 text-red-400 border-red-500/50',
  supporting: 'bg-purple-500/20 text-purple-400 border-purple-500/50',
  minor: 'bg-gray-500/20 text-gray-400 border-gray-500/50',
};

export function CharacterCard({
  character,
  onClick,
  onDelete,
  showActions = true,
}: CharacterCardProps) {
  const [deleting, setDeleting] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [consistencyStatus, setConsistencyStatus] = useState<'consistent' | 'inconsistent' | null>(null);

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (!confirm(`Delete ${character.name}?`)) {
      return;
    }

    setDeleting(true);
    try {
      await characterApi.deleteCharacter(character.id);
      onDelete?.();
    } catch (err) {
      console.error('Failed to delete character:', err);
      alert('Failed to delete character');
    } finally {
      setDeleting(false);
    }
  };

  const handleAnalyze = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setAnalyzing(true);

    try {
      const analysis = await characterApi.analyzeConsistency(character.id);
      setConsistencyStatus(analysis.consistent ? 'consistent' : 'inconsistent');
      
      if (!analysis.consistent) {
        alert(`Found ${analysis.issues.length} consistency issue(s). Check details for more info.`);
      }
    } catch (err) {
      console.error('Failed to analyze consistency:', err);
      alert('Failed to analyze consistency');
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div
      onClick={onClick}
      className={`bg-gray-800 rounded-lg p-4 border border-gray-700 hover:border-indigo-500 transition-colors cursor-pointer ${
        onClick ? 'hover:shadow-lg' : ''
      }`}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-indigo-500/20 flex items-center justify-center">
            <User className="w-5 h-5 text-indigo-400" />
          </div>
          <div>
            <h3 className="font-semibold text-white">{character.name}</h3>
            <span className={`text-xs px-2 py-1 rounded border ${roleColors[character.role] || roleColors.minor}`}>
              {character.role}
            </span>
          </div>
        </div>

        {consistencyStatus && (
          <div className="flex items-center gap-1">
            {consistencyStatus === 'consistent' ? (
              <CheckCircle className="w-4 h-4 text-green-400" />
            ) : (
              <AlertCircle className="w-4 h-4 text-yellow-400" />
            )}
          </div>
        )}
      </div>

      <div className="space-y-2 mb-4">
        <div>
          <p className="text-xs text-gray-400 mb-1">Physical Description</p>
          <p className="text-sm text-gray-300 line-clamp-2">
            {character.profile.physical_description || 'Not specified'}
          </p>
        </div>

        <div>
          <p className="text-xs text-gray-400 mb-1">Personality Traits</p>
          <div className="flex flex-wrap gap-1">
            {character.profile.personality_traits?.slice(0, 3).map((trait, idx) => (
              <span
                key={idx}
                className="text-xs px-2 py-1 bg-gray-700 text-gray-300 rounded"
              >
                {trait}
              </span>
            ))}
            {character.profile.personality_traits?.length > 3 && (
              <span className="text-xs text-gray-500">
                +{character.profile.personality_traits.length - 3} more
              </span>
            )}
          </div>
        </div>

        {character.profile.goals && character.profile.goals.length > 0 && (
          <div>
            <p className="text-xs text-gray-400 mb-1">Primary Goal</p>
            <p className="text-sm text-gray-300">
              {character.profile.goals[0]}
            </p>
          </div>
        )}
      </div>

      {showActions && (
        <div className="flex gap-2 pt-3 border-t border-gray-700">
          <button
            onClick={handleAnalyze}
            disabled={analyzing}
            className="flex-1 px-3 py-1.5 text-xs bg-indigo-600 hover:bg-indigo-700 text-white rounded transition-colors disabled:opacity-50 flex items-center justify-center gap-1"
          >
            {analyzing ? (
              <>
                <span className="animate-spin">⏳</span>
                Analyzing...
              </>
            ) : (
              <>
                <TrendingUp className="w-3 h-3" />
                Check Consistency
              </>
            )}
          </button>
          <button
            onClick={handleDelete}
            disabled={deleting}
            className="px-3 py-1.5 text-xs bg-red-600 hover:bg-red-700 text-white rounded transition-colors disabled:opacity-50"
          >
            {deleting ? '...' : <Trash2 className="w-3 h-3" />}
          </button>
        </div>
      )}
    </div>
  );
}
