import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

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

interface BeatState {
  beats: Beat[];
  originalBeats: Beat[];
  isDirty: boolean;
  history: Beat[][];
  historyIndex: number;
  
  // Actions
  setBeats: (beats: Beat[]) => void;
  updateBeat: (id: number, updates: Partial<Beat>) => void;
  reorderBeats: (newOrder: number[]) => void;
  addBeat: (beat: Beat) => void;
  deleteBeat: (id: number) => void;
  markDirty: () => void;
  markClean: () => void;
  
  // Undo/Redo
  undo: () => void;
  redo: () => void;
  canUndo: () => boolean;
  canRedo: () => boolean;
  saveToHistory: () => void;
  
  // Reset
  reset: () => void;
}

const MAX_HISTORY = 50;

export const useBeatStore = create<BeatState>()(
  devtools(
    (set, get) => ({
      beats: [],
      originalBeats: [],
      isDirty: false,
      history: [],
      historyIndex: -1,

      setBeats: (beats) => {
        set({
          beats: [...beats],
          originalBeats: [...beats],
          isDirty: false,
          history: [[...beats]],
          historyIndex: 0,
        });
      },

      updateBeat: (id, updates) => {
        const { beats, saveToHistory } = get();
        const updatedBeats = beats.map((beat) =>
          beat.id === id ? { ...beat, ...updates } : beat
        );
        
        set({
          beats: updatedBeats,
          isDirty: true,
        });
        
        saveToHistory();
      },

      reorderBeats: (newOrder) => {
        const { beats, saveToHistory } = get();
        const beatMap = new Map(beats.map((b) => [b.id, b]));
        const reorderedBeats = newOrder
          .map((id) => beatMap.get(id))
          .filter((b): b is Beat => b !== undefined)
          .map((beat, index) => ({ ...beat, beat_index: index }));
        
        set({
          beats: reorderedBeats,
          isDirty: true,
        });
        
        saveToHistory();
      },

      addBeat: (beat) => {
        const { beats, saveToHistory } = get();
        const newBeats = [...beats, beat].sort((a, b) => a.beat_index - b.beat_index);
        
        set({
          beats: newBeats,
          isDirty: true,
        });
        
        saveToHistory();
      },

      deleteBeat: (id) => {
        const { beats, saveToHistory } = get();
        const filteredBeats = beats
          .filter((b) => b.id !== id)
          .map((beat, index) => ({ ...beat, beat_index: index }));
        
        set({
          beats: filteredBeats,
          isDirty: true,
        });
        
        saveToHistory();
      },

      markDirty: () => set({ isDirty: true }),
      markClean: () => set({ isDirty: false }),

      saveToHistory: () => {
        const { beats, history, historyIndex } = get();
        const newHistory = history.slice(0, historyIndex + 1);
        newHistory.push([...beats]);
        
        // Limit history size
        if (newHistory.length > MAX_HISTORY) {
          newHistory.shift();
        }
        
        set({
          history: newHistory,
          historyIndex: newHistory.length - 1,
        });
      },

      undo: () => {
        const { history, historyIndex } = get();
        if (historyIndex > 0) {
          set({
            beats: [...history[historyIndex - 1]],
            historyIndex: historyIndex - 1,
            isDirty: true,
          });
        }
      },

      redo: () => {
        const { history, historyIndex } = get();
        if (historyIndex < history.length - 1) {
          set({
            beats: [...history[historyIndex + 1]],
            historyIndex: historyIndex + 1,
            isDirty: true,
          });
        }
      },

      canUndo: () => {
        const { historyIndex } = get();
        return historyIndex > 0;
      },

      canRedo: () => {
        const { history, historyIndex } = get();
        return historyIndex < history.length - 1;
      },

      reset: () => {
        set({
          beats: [],
          originalBeats: [],
          isDirty: false,
          history: [],
          historyIndex: -1,
        });
      },
    }),
    { name: 'BeatStore' }
  )
);

