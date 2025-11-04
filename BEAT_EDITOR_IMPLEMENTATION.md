# Beat Editor Implementation Summary

This document describes the interactive beat editor implementation for StoryWeave AI.

## Backend API Endpoints

### Added to `main.py`:

1. **GET `/stories/{story_id}/beats`**
   - Returns all beats for a story, ordered by `beat_index`

2. **PUT `/beats/{beat_id}`**
   - Updates a beat with partial data (title, goal, conflict, outcome, beat_index)

3. **DELETE `/beats/{beat_id}`**
   - Deletes a beat

4. **POST `/stories/{story_id}/beats/reorder`**
   - Reorders beats by updating their `beat_index` values
   - Takes `beat_ids` array in the new order

5. **POST `/stories/{story_id}/beats`**
   - Creates a new beat for a story

## Frontend Components

### File Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── BeatEditor.tsx          # Main editor component
│   │   ├── BeatCard.tsx            # Individual beat card
│   │   └── BeatEditor.example.tsx  # Usage example
│   ├── hooks/
│   │   └── useBeatEditor.ts        # Custom hook for beat management
│   ├── stores/
│   │   └── beatStore.ts            # Zustand store with undo/redo
│   ├── lib/
│   │   └── api.ts                  # Axios API client
│   └── types/
│       └── beat.ts                 # TypeScript type definitions
├── package.json
└── README.md
```

### Key Features

#### 1. Drag-and-Drop Reordering
- Uses `@dnd-kit/core` and `@dnd-kit/sortable`
- Smooth animations and visual feedback
- Optimistic updates with backend sync

#### 2. Inline Editing
- Click any field (title, goal, conflict, outcome) to edit
- Auto-saves with 1-second debounce
- Keyboard shortcuts: Cmd+Enter to save, Escape to cancel

#### 3. Undo/Redo System
- Full history tracking with Zustand store
- Maximum 50 history entries
- Keyboard shortcuts:
  - `Cmd+Z` / `Ctrl+Z`: Undo
  - `Cmd+Shift+Z` / `Ctrl+Shift+Z`: Redo

#### 4. Visual Design
- Color-coded beats by type:
  - Hook/Opening: Blue
  - Inciting Incident: Purple
  - Crisis: Red
  - Climax: Orange
  - Resolution: Green
  - Default: Indigo
- Beat number badges
- Drag handles (⋮⋮)
- Collapsible sections for goal/conflict/outcome
- Hover effects and transitions

#### 5. State Management
- Zustand store for client-side state
- Optimistic updates (UI updates immediately)
- Debounced auto-save to backend
- Tracks dirty state (unsaved changes)
- History management for undo/redo

## Installation

```bash
cd frontend
npm install
```

## Dependencies

- `@dnd-kit/core`: Drag-and-drop functionality
- `@dnd-kit/sortable`: Sortable list components
- `@dnd-kit/utilities`: Utility functions
- `axios`: HTTP client
- `lucide-react`: Icons
- `zustand`: State management
- `react`: React library
- `react-dom`: React DOM

## Usage

```tsx
import { BeatEditor } from './components/BeatEditor';

function App() {
  return (
    <BeatEditor 
      storyId={123}
      onExpandScene={(beatId) => {
        // Handle scene expansion
      }}
    />
  );
}
```

## API Integration

The component automatically handles:
- Loading beats on mount
- Saving changes with debouncing
- Reordering beats via drag-and-drop
- Creating new beats
- Deleting beats with confirmation

## Keyboard Shortcuts

- `Cmd+Z` / `Ctrl+Z`: Undo
- `Cmd+Shift+Z` / `Ctrl+Shift+Z`: Redo
- `Cmd+S` / `Ctrl+S`: Save all changes immediately
- `Cmd+Enter` / `Ctrl+Enter`: Save current field (when editing)
- `Escape`: Cancel editing

## Environment Variables

Set in `.env`:
```
VITE_API_URL=http://localhost:8080
```

## Testing

To test the implementation:

1. Start the backend server
2. Navigate to a story with beats
3. Try dragging beats to reorder
4. Click fields to edit inline
5. Test undo/redo functionality
6. Verify auto-save works

## Future Enhancements

- Beat templates/presets
- Duplicate beat functionality
- Beat notes/annotations
- Export/import beats
- Collaborative editing (WebSocket)
- Beat validation rules
- Custom beat types

