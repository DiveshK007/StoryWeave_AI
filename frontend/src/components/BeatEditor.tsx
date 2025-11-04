import React, { useEffect, useCallback } from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { BeatCard } from './BeatCard';
import { useBeatEditor } from '../hooks/useBeatEditor';
import { useBeatStore } from '../stores/beatStore';
import { Plus, Save, RotateCcw, RotateCw } from 'lucide-react';

interface BeatEditorProps {
  storyId: number;
  onExpandScene?: (beatId: number) => void;
}

export const BeatEditor: React.FC<BeatEditorProps> = ({ storyId, onExpandScene }) => {
  const {
    beats,
    loadBeats,
    updateBeat,
    reorderBeats,
    addBeat,
    deleteBeat,
    saveAll,
    isDirty,
  } = useBeatEditor({ storyId });

  const { undo, redo, canUndo, canRedo } = useBeatStore();

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  // Load beats on mount
  useEffect(() => {
    loadBeats();
  }, [loadBeats]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd+Z or Ctrl+Z for undo
      if ((e.metaKey || e.ctrlKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        if (canUndo()) undo();
      }
      // Cmd+Shift+Z or Ctrl+Shift+Z for redo
      if ((e.metaKey || e.ctrlKey) && e.key === 'z' && e.shiftKey) {
        e.preventDefault();
        if (canRedo()) redo();
      }
      // Cmd+S or Ctrl+S for save
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault();
        saveAll();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [canUndo, canRedo, undo, redo, saveAll]);

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const { active, over } = event;

      if (over && active.id !== over.id) {
        const oldIndex = beats.findIndex((b) => b.id === active.id);
        const newIndex = beats.findIndex((b) => b.id === over.id);

        const newOrder = arrayMove(beats, oldIndex, newIndex);
        const beatIds = newOrder.map((b) => b.id);
        reorderBeats(beatIds);
      }
    },
    [beats, reorderBeats]
  );

  const handleAddBeat = useCallback(async () => {
    try {
      await addBeat();
    } catch (error) {
      console.error('Failed to add beat:', error);
    }
  }, [addBeat]);

  const handleDeleteBeat = useCallback(
    async (beatId: number) => {
      try {
        await deleteBeat(beatId);
      } catch (error) {
        console.error('Failed to delete beat:', error);
      }
    },
    [deleteBeat]
  );

  const handleUpdateBeat = useCallback(
    (beatId: number, updates: Partial<Beat>) => {
      updateBeat(beatId, updates);
    },
    [updateBeat]
  );

  return (
    <div className="w-full max-w-4xl mx-auto p-6">
      {/* Header with Actions */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white mb-1">Story Beats</h2>
          <p className="text-sm text-gray-400">
            Drag to reorder • Click to edit • Auto-saves as you type
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Undo/Redo */}
          <button
            onClick={undo}
            disabled={!canUndo()}
            className="p-2 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded transition-colors"
            title="Undo (Cmd+Z)"
          >
            <RotateCcw size={18} />
          </button>
          <button
            onClick={redo}
            disabled={!canRedo()}
            className="p-2 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded transition-colors"
            title="Redo (Cmd+Shift+Z)"
          >
            <RotateCw size={18} />
          </button>

          {/* Save Button */}
          {isDirty && (
            <button
              onClick={saveAll}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors flex items-center gap-2"
              title="Save all changes (Cmd+S)"
            >
              <Save size={18} />
              <span>Save</span>
            </button>
          )}

          {/* Add Beat Button */}
          <button
            onClick={handleAddBeat}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors flex items-center gap-2"
          >
            <Plus size={18} />
            <span>Add Beat</span>
          </button>
        </div>
      </div>

      {/* Beats List */}
      {beats.length === 0 ? (
        <div className="text-center py-12 bg-gray-800/50 rounded-lg border border-gray-700">
          <p className="text-gray-400 mb-4">No beats yet. Create your first beat to get started!</p>
          <button
            onClick={handleAddBeat}
            className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors inline-flex items-center gap-2"
          >
            <Plus size={20} />
            <span>Add First Beat</span>
          </button>
        </div>
      ) : (
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragEnd={handleDragEnd}
        >
          <SortableContext
            items={beats.map((b) => b.id)}
            strategy={verticalListSortingStrategy}
          >
            <div className="space-y-4">
              {beats.map((beat) => (
                <BeatCard
                  key={beat.id}
                  beat={beat}
                  onUpdate={handleUpdateBeat}
                  onDelete={handleDeleteBeat}
                  onExpandScene={onExpandScene}
                />
              ))}
            </div>
          </SortableContext>
        </DndContext>
      )}

      {/* Status Indicator */}
      {isDirty && (
        <div className="mt-4 text-center">
          <span className="inline-flex items-center gap-2 text-sm text-yellow-400">
            <span className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse"></span>
            Unsaved changes
          </span>
        </div>
      )}
    </div>
  );
};

