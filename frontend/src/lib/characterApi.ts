import { apiCall } from './api';
import type {
  Character,
  CharacterProfile,
  Relationship,
  CharacterMention,
  ConsistencyAnalysis,
  CharacterRole,
  RelationshipType,
} from '../types/character';

export interface CharacterGenerateRequest {
  story_id: number;
  name: string;
  role: CharacterRole;
}

export interface CharacterUpdateRequest {
  name?: string;
  role?: CharacterRole;
  profile_json?: CharacterProfile;
}

export interface RelationshipCreateRequest {
  character_a_id: number;
  character_b_id: number;
  type: RelationshipType;
  strength?: number;
  notes?: string;
}

export const characterApi = {
  /**
   * Generate a new character with AI-generated profile
   */
  async generateCharacter(data: CharacterGenerateRequest): Promise<Character> {
    return apiCall('POST', '/characters/generate', data);
  },

  /**
   * Get all characters for a story
   */
  async getStoryCharacters(storyId: number): Promise<{ characters: Character[] }> {
    return apiCall('GET', `/characters/stories/${storyId}/characters`);
  },

  /**
   * Get character details with relationships
   */
  async getCharacter(characterId: number): Promise<Character & { relationships: Relationship[] }> {
    return apiCall('GET', `/characters/${characterId}`);
  },

  /**
   * Update a character
   */
  async updateCharacter(
    characterId: number,
    data: CharacterUpdateRequest
  ): Promise<Character> {
    return apiCall('PUT', `/characters/${characterId}`, data);
  },

  /**
   * Delete a character
   */
  async deleteCharacter(characterId: number): Promise<{ success: boolean; message: string }> {
    return apiCall('DELETE', `/characters/${characterId}`);
  },

  /**
   * Analyze character consistency across scenes
   */
  async analyzeConsistency(characterId: number): Promise<ConsistencyAnalysis> {
    return apiCall('POST', `/characters/${characterId}/analyze-consistency`);
  },

  /**
   * Get all mentions of a character
   */
  async getMentions(characterId: number): Promise<{
    character_id: number;
    mentions: CharacterMention[];
  }> {
    return apiCall('GET', `/characters/${characterId}/mentions`);
  },

  /**
   * Create a relationship between two characters
   */
  async createRelationship(data: RelationshipCreateRequest): Promise<Relationship> {
    return apiCall('POST', '/characters/relationships', data);
  },
};
