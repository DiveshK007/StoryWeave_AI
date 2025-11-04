import React from 'react';
import { Users, Circle } from 'lucide-react';
import type { PresenceUser } from '../types/collaboration';

interface UserPresenceProps {
  users: PresenceUser[];
  currentUserId: number;
}

export function UserPresence({ users, currentUserId }: UserPresenceProps) {
  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

  const getColorForUser = (userId: number) => {
    return colors[userId % colors.length];
  };

  return (
    <div className="flex items-center gap-2">
      <Users className="w-4 h-4 text-gray-400" />
      <div className="flex items-center gap-2">
        {users.map((user) => (
          <div
            key={user.user_id}
            className="flex items-center gap-1.5"
            title={user.user_name}
          >
            <div className="relative">
              <div
                className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-semibold"
                style={{ backgroundColor: getColorForUser(user.user_id) }}
              >
                {user.user_name.charAt(0).toUpperCase()}
              </div>
              {user.user_id === currentUserId && (
                <Circle className="w-3 h-3 text-green-400 absolute -bottom-0.5 -right-0.5 fill-current" />
              )}
            </div>
          </div>
        ))}
      </div>
      {users.length > 0 && (
        <span className="text-xs text-gray-400">
          {users.length} {users.length === 1 ? 'user' : 'users'} online
        </span>
      )}
    </div>
  );
}
