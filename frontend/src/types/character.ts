export type CharacterRole = 'protagonist' | 'antagonist' | 'supporting' | 'minor';

export type RelationshipType = 'family' | 'friend' | 'enemy' | 'romance' | 'mentor' | 'rival' | 'ally' | 'other';

export interface CharacterProfile {
  physical_description: string;
  personality_traits: string[];
  backstory: string;
  goals: string[];
  motivations: string;
  fears: string[];
  flaws: string[];
  strengths?: string[];
  speech_patterns?: string;
  abilities?: string[];
  knowledge?: string;
  character_arc?: string;
}

export interface Character {
  id: number;
  name: string;
  role: CharacterRole;
  profile: CharacterProfile;
  created_at?: string;
  mention_count?: number;
  relationships?: Relationship[];
}

export interface Relationship {
  id: number;
  character_id: number;
  character_name: string;
  type: RelationshipType;
  strength: number;
  notes?: string;
}

export interface CharacterMention {
  id: number;
  scene_id: number;
  context: string;
  mention_type: 'dialogue' | 'action' | 'description';
  created_at?: string;
}

export interface ConsistencyIssue {
  type: 'physical' | 'speech' | 'behavior' | 'ability' | 'knowledge';
  severity: 'low' | 'medium' | 'high';
  description: string;
  scene_index: number;
  evidence: string;
}

export interface ConsistencyAnalysis {
  character_id: number;
  character_name: string;
  consistent: boolean;
  issues: ConsistencyIssue[];
  mentions: Array<{
    scene_index: number;
    context: string;
    mention_type: 'dialogue' | 'action' | 'description';
    consistency: 'consistent' | 'inconsistent';
  }>;
}
