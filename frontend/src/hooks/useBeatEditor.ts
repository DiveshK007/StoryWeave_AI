import { useCallback, useEffect, useRef } from 'react';
import { useBeatStore, Beat } from '../stores/beatStore';
import { api } from '../lib/api';
import { getDemoBeats } from '../lib/demoData';

interface UseBeatEditorOptions {
  storyId: number;
  debounceMs?: number;
}

export function useBeatEditor({ storyId, debounceMs = 1000 }: UseBeatEditorOptions) {
  const {
    beats,
    setBeats,
    updateBeat: updateBeatStore,
    reorderBeats: reorderBeatsStore,
    addBeat: addBeatStore,
    deleteBeat: deleteBeatStore,
    markClean,
    isDirty,
  } = useBeatStore();

  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const pendingUpdatesRef = useRef<Map<number, Partial<Beat>>>(new Map());

  // Load beats from API
  const loadBeats = useCallback(async () => {
    try {
      const response = await api.get(`/stories/${storyId}/beats`);
      const beats = response.data?.beats || response.data || [];
      setBeats(beats);
    } catch (error: any) {
      console.warn('API unavailable, using demo beats:', error);
      // Fall back to demo data
      const demoBeats = getDemoBeats(storyId);
      if (demoBeats.length > 0) {
        setBeats(demoBeats as Beat[]);
      } else {
        setBeats([]);
      }
    }
  }, [storyId, setBeats]);

  // Debounced save function
  const saveBeat = useCallback(
    async (beatId: number, updates: Partial<Beat>) => {
      // Store pending update
      const existing = pendingUpdatesRef.current.get(beatId) || {};
      pendingUpdatesRef.current.set(beatId, { ...existing, ...updates });

      // Clear existing timer
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }

      // Set new timer
      debounceTimerRef.current = setTimeout(async () => {
        const pendingUpdates = pendingUpdatesRef.current;
        pendingUpdatesRef.current = new Map();

        // Save all pending updates
        const promises = Array.from(pendingUpdates.entries()).map(([id, updates]) =>
          api.put(`/beats/${id}`, updates).catch((error: any) => {
            if (error.code === 'ERR_NETWORK' || error.response?.status >= 500) {
              // Demo mode - just mark as clean since we can't save
              console.warn(`Demo mode: Beat ${id} saved locally`);
            } else {
              console.error(`Failed to save beat ${id}:`, error);
              // Re-add failed update
              pendingUpdatesRef.current.set(id, updates);
            }
          })
        );

        await Promise.all(promises);
        markClean();
      }, debounceMs);
    },
    [debounceMs, markClean]
  );

  // Update beat (optimistic update + debounced save)
  const updateBeat = useCallback(
    (beatId: number, updates: Partial<Beat>) => {
      updateBeatStore(beatId, updates);
      saveBeat(beatId, updates);
    },
    [updateBeatStore, saveBeat]
  );

  // Reorder beats
  const reorderBeats = useCallback(
    async (newOrder: number[]) => {
      // Optimistic update
      reorderBeatsStore(newOrder);

      try {
        await api.post(`/stories/${storyId}/beats/reorder`, {
          beat_ids: newOrder,
        });
        markClean();
      } catch (error) {
        console.error('Failed to reorder beats:', error);
        // Reload on error
        await loadBeats();
        throw error;
      }
    },
    [storyId, reorderBeatsStore, markClean, loadBeats]
  );

  // Add new beat
  const addBeat = useCallback(async () => {
    try {
      const response = await api.post(`/stories/${storyId}/beats`, {
        title: 'New Beat',
        goal: null,
        conflict: null,
        outcome: null,
      });

      const newBeat = response.data;
      addBeatStore(newBeat);
      markClean();
      return newBeat;
    } catch (error) {
      console.error('Failed to create beat:', error);
      throw error;
    }
  }, [storyId, addBeatStore, markClean]);

  // Delete beat
  const deleteBeat = useCallback(
    async (beatId: number) => {
      // Optimistic update
      deleteBeatStore(beatId);

      try {
        await api.delete(`/beats/${beatId}`);
        markClean();
      } catch (error) {
        console.error('Failed to delete beat:', error);
        // Reload on error
        await loadBeats();
        throw error;
      }
    },
    [deleteBeatStore, markClean, loadBeats]
  );

  // Save all changes immediately
  const saveAll = useCallback(async () => {
    // Clear debounce timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
      debounceTimerRef.current = null;
    }

    // Save all pending updates
    const pendingUpdates = pendingUpdatesRef.current;
    pendingUpdatesRef.current = new Map();

    const promises = Array.from(pendingUpdates.entries()).map(([id, updates]) =>
      api.put(`/beats/${id}`, updates)
    );

    await Promise.all(promises);
    markClean();
  }, [markClean]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  return {
    beats,
    isDirty,
    loadBeats,
    updateBeat,
    reorderBeats,
    addBeat,
    deleteBeat,
    saveAll,
  };
}

