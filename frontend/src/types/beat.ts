/**
 * Type definitions for Beat-related entities
 */

export interface Beat {
  id: number;
  beat_index: number;
  title: string;
  goal: string | null;
  conflict: string | null;
  outcome: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface BeatUpdate {
  title?: string;
  goal?: string | null;
  conflict?: string | null;
  outcome?: string | null;
  beat_index?: number;
}

export interface BeatReorderRequest {
  beat_ids: number[];
}

export type BeatType = 
  | 'hook'
  | 'inciting-incident'
  | 'first-threshold'
  | 'midpoint'
  | 'crisis'
  | 'climax'
  | 'resolution'
  | 'custom';

