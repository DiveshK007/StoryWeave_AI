import { useEffect, useRef, useState, useCallback } from 'react';
import type { WebSocketMessage, PresenceUser, BeatEdit, ChatMessage } from '../types/collaboration';

interface UseWebSocketOptions {
  storyId: number;
  userId: number;
  userName: string;
  userEmail: string;
  onMessage?: (message: WebSocketMessage) => void;
  onError?: (error: Event) => void;
  onOpen?: () => void;
  onClose?: () => void;
}

export function useWebSocket({
  storyId,
  userId,
  userName,
  userEmail,
  onMessage,
  onError,
  onOpen,
  onClose,
}: UseWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const [users, setUsers] = useState<PresenceUser[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}/collaboration/ws/story/${storyId}?user_id=${userId}&user_name=${encodeURIComponent(userName)}&user_email=${encodeURIComponent(userEmail)}`;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        reconnectAttempts.current = 0;
        onOpen?.();
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          
          if (message.type === 'presence_update' && message.users) {
            setUsers(message.users);
          }
          
          onMessage?.(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        onError?.(error);
      };

      ws.onclose = () => {
        setIsConnected(false);
        wsRef.current = null;
        onClose?.();

        // Attempt to reconnect
        if (reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current += 1;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        }
      };
    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
    }
  }, [storyId, userId, userName, userEmail, onMessage, onError, onOpen, onClose]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    reconnectAttempts.current = maxReconnectAttempts; // Prevent reconnection
    wsRef.current?.close();
    wsRef.current = null;
    setIsConnected(false);
  }, []);

  const sendMessage = useCallback((message: WebSocketMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      return true;
    }
    return false;
  }, []);

  const sendEdit = useCallback((beatId: number, changes: BeatEdit['changes']) => {
    return sendMessage({
      type: 'edit',
      beat_id: beatId,
      changes,
      timestamp: new Date().toISOString(),
    });
  }, [sendMessage]);

  const sendCursorMove = useCallback((beatId: number, position: number) => {
    return sendMessage({
      type: 'cursor_move',
      beat_id: beatId,
      position,
      timestamp: new Date().toISOString(),
    });
  }, [sendMessage]);

  const sendChat = useCallback((message: string) => {
    return sendMessage({
      type: 'chat',
      message,
      timestamp: new Date().toISOString(),
    });
  }, [sendMessage]);

  const lockBeat = useCallback((beatId: number, durationMinutes: number = 30) => {
    return sendMessage({
      type: 'beat_lock',
      beat_id: beatId,
      duration_minutes: durationMinutes,
    });
  }, [sendMessage]);

  const unlockBeat = useCallback((beatId: number) => {
    return sendMessage({
      type: 'beat_unlock',
      beat_id: beatId,
    });
  }, [sendMessage]);

  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    users,
    sendMessage,
    sendEdit,
    sendCursorMove,
    sendChat,
    lockBeat,
    unlockBeat,
    reconnect: connect,
    disconnect,
  };
}
