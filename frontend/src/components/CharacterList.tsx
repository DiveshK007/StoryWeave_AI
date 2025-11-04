import React, { useState, useEffect } from 'react';
import { Users, Loader2, AlertCircle } from 'lucide-react';
import { characterApi } from '../lib/characterApi';
import { CharacterCard } from './CharacterCard';
import { CharacterCreator } from './CharacterCreator';
import { getDemoCharacters } from '../lib/demoData';
import type { Character } from '../types/character';

interface CharacterListProps {
  storyId: number;
  onCharacterClick?: (character: Character) => void;
}

export function CharacterList({ storyId, onCharacterClick }: CharacterListProps) {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadCharacters = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await characterApi.getStoryCharacters(storyId);
      setCharacters(response.characters);
    } catch (err: any) {
      console.warn('API unavailable, using demo characters:', err);
      // Fall back to demo data for story ID 1
      if (storyId === 1) {
        const demoChars = getDemoCharacters(storyId);
        setCharacters(demoChars as Character[]);
      } else {
        setError('Failed to load characters');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (storyId) {
      loadCharacters();
    }
  }, [storyId]);

  const handleCharacterCreated = (newCharacter: Character) => {
    setCharacters((prev) => [...prev, newCharacter]);
  };

  const handleCharacterDeleted = (characterId: number) => {
    setCharacters((prev) => prev.filter((c) => c.id !== characterId));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="w-6 h-6 animate-spin text-indigo-400" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-500/20 border border-red-500/50 rounded-lg">
        <div className="flex items-center gap-2 text-red-400">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-4">
        <Users className="w-5 h-5 text-primary-400" />
        <h2 className="text-xl font-semibold text-text-primary">
          Characters ({characters.length})
        </h2>
      </div>

      {characters.length === 0 ? (
        <div className="text-center py-8 text-text-secondary">
          <Users className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>No characters yet. Create one to get started!</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {characters.map((character) => (
            <CharacterCard
              key={character.id}
              character={character}
              onClick={() => onCharacterClick?.(character)}
              onDelete={() => handleCharacterDeleted(character.id)}
            />
          ))}
        </div>
      )}

      <CharacterCreator
        storyId={storyId}
        onCharacterCreated={handleCharacterCreated}
      />
    </div>
  );
}

// Export handler for use in parent
CharacterList.refresh = () => {};
