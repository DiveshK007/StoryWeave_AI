import React, { useState, useRef, useEffect } from 'react';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVertical, Edit2, Trash2, ChevronDown, ChevronUp } from 'lucide-react';
import { Beat } from '../stores/beatStore';

interface BeatCardProps {
  beat: Beat;
  onUpdate: (id: number, updates: Partial<Beat>) => void;
  onDelete: (id: number) => void;
  onExpandScene?: (beatId: number) => void;
}

// Beat type color mapping
const getBeatColor = (title: string): string => {
  const lowerTitle = title.toLowerCase();
  if (lowerTitle.includes('hook') || lowerTitle.includes('opening')) {
    return 'bg-blue-500/20 border-blue-500/50 text-blue-200';
  }
  if (lowerTitle.includes('inciting') || lowerTitle.includes('incident')) {
    return 'bg-purple-500/20 border-purple-500/50 text-purple-200';
  }
  if (lowerTitle.includes('crisis') || lowerTitle.includes('dark')) {
    return 'bg-red-500/20 border-red-500/50 text-red-200';
  }
  if (lowerTitle.includes('climax')) {
    return 'bg-orange-500/20 border-orange-500/50 text-orange-200';
  }
  if (lowerTitle.includes('resolution') || lowerTitle.includes('ending')) {
    return 'bg-green-500/20 border-green-500/50 text-green-200';
  }
  return 'bg-indigo-500/20 border-indigo-500/50 text-indigo-200';
};

export const BeatCard: React.FC<BeatCardProps> = ({
  beat,
  onUpdate,
  onDelete,
  onExpandScene,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [expandedSections, setExpandedSections] = useState({
    goal: false,
    conflict: false,
    outcome: false,
  });
  const [editValues, setEditValues] = useState({
    title: beat.title,
    goal: beat.goal || '',
    conflict: beat.conflict || '',
    outcome: beat.outcome || '',
  });

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: beat.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const titleInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isEditing && titleInputRef.current) {
      titleInputRef.current.focus();
      titleInputRef.current.select();
    }
  }, [isEditing]);

  const handleSave = () => {
    onUpdate(beat.id, {
      title: editValues.title,
      goal: editValues.goal || null,
      conflict: editValues.conflict || null,
      outcome: editValues.outcome || null,
    });
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditValues({
      title: beat.title,
      goal: beat.goal || '',
      conflict: beat.conflict || '',
      outcome: beat.outcome || '',
    });
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent, field?: string) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSave();
    }
    if (e.key === 'Escape') {
      handleCancel();
    }
  };

  const toggleSection = (section: 'goal' | 'conflict' | 'outcome') => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const beatColor = getBeatColor(beat.title);

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`
        group relative bg-gray-800/50 border rounded-lg p-4
        transition-all duration-200
        ${beatColor}
        ${isDragging ? 'shadow-2xl scale-105 z-50' : 'hover:bg-gray-800/70'}
        ${isEditing ? 'ring-2 ring-indigo-400' : ''}
      `}
    >
      {/* Drag Handle */}
      <div
        {...attributes}
        {...listeners}
        className="absolute left-2 top-4 cursor-grab active:cursor-grabbing text-gray-400 hover:text-gray-200 transition-colors"
      >
        <GripVertical size={20} />
      </div>

      {/* Beat Number Badge */}
      <div className="absolute right-4 top-4">
        <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-indigo-600 text-white text-sm font-bold">
          {beat.beat_index + 1}
        </span>
      </div>

      {/* Title Section */}
      <div className="ml-8 mr-12 mb-3">
        {isEditing ? (
          <input
            ref={titleInputRef}
            type="text"
            value={editValues.title}
            onChange={(e) => setEditValues({ ...editValues, title: e.target.value })}
            onBlur={handleSave}
            onKeyDown={(e) => handleKeyDown(e)}
            className="w-full bg-gray-900/50 border border-indigo-500/50 rounded px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-indigo-400"
            placeholder="Beat title..."
          />
        ) : (
          <h3
            className="text-lg font-semibold text-white cursor-text hover:text-indigo-300 transition-colors"
            onClick={() => setIsEditing(true)}
            title="Click to edit"
          >
            {beat.title}
          </h3>
        )}
      </div>

      {/* Collapsible Sections */}
      <div className="space-y-2 ml-8">
        {/* Goal Section */}
        <div className="border-t border-gray-700/50 pt-2">
          <button
            onClick={() => toggleSection('goal')}
            className="w-full flex items-center justify-between text-sm text-gray-300 hover:text-white transition-colors"
          >
            <span className="font-medium">Goal</span>
            {expandedSections.goal ? (
              <ChevronUp size={16} />
            ) : (
              <ChevronDown size={16} />
            )}
          </button>
          {expandedSections.goal && (
            <div className="mt-2">
              {isEditing ? (
                <textarea
                  value={editValues.goal}
                  onChange={(e) => setEditValues({ ...editValues, goal: e.target.value })}
                  onBlur={handleSave}
                  onKeyDown={(e) => handleKeyDown(e, 'goal')}
                  className="w-full bg-gray-900/50 border border-indigo-500/50 rounded px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-none"
                  placeholder="What does the character want?"
                  rows={2}
                />
              ) : (
                <p
                  className="text-sm text-gray-400 cursor-text hover:text-gray-300 transition-colors min-h-[2rem]"
                  onClick={() => setIsEditing(true)}
                >
                  {beat.goal || <span className="italic text-gray-500">Click to add goal...</span>}
                </p>
              )}
            </div>
          )}
        </div>

        {/* Conflict Section */}
        <div className="border-t border-gray-700/50 pt-2">
          <button
            onClick={() => toggleSection('conflict')}
            className="w-full flex items-center justify-between text-sm text-gray-300 hover:text-white transition-colors"
          >
            <span className="font-medium">Conflict</span>
            {expandedSections.conflict ? (
              <ChevronUp size={16} />
            ) : (
              <ChevronDown size={16} />
            )}
          </button>
          {expandedSections.conflict && (
            <div className="mt-2">
              {isEditing ? (
                <textarea
                  value={editValues.conflict}
                  onChange={(e) => setEditValues({ ...editValues, conflict: e.target.value })}
                  onBlur={handleSave}
                  onKeyDown={(e) => handleKeyDown(e, 'conflict')}
                  className="w-full bg-gray-900/50 border border-indigo-500/50 rounded px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-none"
                  placeholder="What obstacle stands in the way?"
                  rows={2}
                />
              ) : (
                <p
                  className="text-sm text-gray-400 cursor-text hover:text-gray-300 transition-colors min-h-[2rem]"
                  onClick={() => setIsEditing(true)}
                >
                  {beat.conflict || (
                    <span className="italic text-gray-500">Click to add conflict...</span>
                  )}
                </p>
              )}
            </div>
          )}
        </div>

        {/* Outcome Section */}
        <div className="border-t border-gray-700/50 pt-2">
          <button
            onClick={() => toggleSection('outcome')}
            className="w-full flex items-center justify-between text-sm text-gray-300 hover:text-white transition-colors"
          >
            <span className="font-medium">Outcome</span>
            {expandedSections.outcome ? (
              <ChevronUp size={16} />
            ) : (
              <ChevronDown size={16} />
            )}
          </button>
          {expandedSections.outcome && (
            <div className="mt-2">
              {isEditing ? (
                <textarea
                  value={editValues.outcome}
                  onChange={(e) => setEditValues({ ...editValues, outcome: e.target.value })}
                  onBlur={handleSave}
                  onKeyDown={(e) => handleKeyDown(e, 'outcome')}
                  className="w-full bg-gray-900/50 border border-indigo-500/50 rounded px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-none"
                  placeholder="What happens as a result?"
                  rows={2}
                />
              ) : (
                <p
                  className="text-sm text-gray-400 cursor-text hover:text-gray-300 transition-colors min-h-[2rem]"
                  onClick={() => setIsEditing(true)}
                >
                  {beat.outcome || (
                    <span className="italic text-gray-500">Click to add outcome...</span>
                  )}
                </p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="mt-4 flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
        {onExpandScene && (
          <button
            onClick={() => onExpandScene(beat.id)}
            className="px-3 py-1.5 text-xs bg-indigo-600 hover:bg-indigo-700 text-white rounded transition-colors"
            title="Expand scene"
          >
            Expand Scene
          </button>
        )}
        <button
          onClick={() => setIsEditing(!isEditing)}
          className="p-1.5 text-gray-400 hover:text-indigo-400 hover:bg-gray-700/50 rounded transition-colors"
          title="Edit beat"
        >
          <Edit2 size={16} />
        </button>
        <button
          onClick={() => {
            if (window.confirm(`Delete "${beat.title}"?`)) {
              onDelete(beat.id);
            }
          }}
          className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-gray-700/50 rounded transition-colors"
          title="Delete beat"
        >
          <Trash2 size={16} />
        </button>
      </div>
    </div>
  );
};

