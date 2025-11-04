export type MessageType = 
  | 'edit'
  | 'cursor_move'
  | 'presence'
  | 'chat'
  | 'beat_lock'
  | 'beat_unlock'
  | 'comment'
  | 'notification'
  | 'presence_update'
  | 'initial_state'
  | 'error';

export type PermissionRole = 'owner' | 'editor' | 'viewer';

export interface WebSocketMessage {
  type: MessageType;
  [key: string]: any;
}

export interface PresenceUser {
  user_id: number;
  user_name: string;
  user_email: string;
  connected_at: string;
}

export interface CursorPosition {
  beat_id: number;
  position: number;
  user_id: number;
  user_name: string;
}

export interface BeatEdit {
  beat_id: number;
  changes: {
    title?: string;
    goal?: string;
    conflict?: string;
    outcome?: string;
  };
  user_id: number;
  user_name: string;
}

export interface BeatLock {
  beat_id: number;
  locked_by: number;
  locked_by_name: string;
  expires_at?: string;
}

export interface ChatMessage {
  message: string;
  user_id: number;
  user_name: string;
  timestamp: string;
}

export interface Comment {
  id: number;
  content: string;
  user_id: number;
  beat_id?: number;
  scene_id?: number;
  parent_comment_id?: number;
  resolved: boolean;
  created_at: string;
}

export interface StoryPermission {
  user_id: number;
  role: PermissionRole;
  invited_by?: number;
  created_at: string;
}
