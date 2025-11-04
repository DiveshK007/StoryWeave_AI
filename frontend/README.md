# StoryWeave AI - Beat Editor

Interactive beat editor component for StoryWeave AI with drag-and-drop, inline editing, and undo/redo functionality.

## Features

- **Drag-and-Drop Reordering**: Use @dnd-kit/core for smooth beat reordering
- **Inline Editing**: Click any field to edit directly
- **Auto-Save**: Changes are automatically saved with debouncing (1 second delay)
- **Undo/Redo**: Full undo/redo support with keyboard shortcuts
- **Visual Feedback**: Color-coded beats by type, drag indicators, hover effects
- **Optimistic Updates**: UI updates immediately, syncs with backend

## Installation

```bash
npm install
```

## Usage

```tsx
import { BeatEditor } from './components/BeatEditor';

function App() {
  return (
    <BeatEditor 
      storyId={123}
      onExpandScene={(beatId) => {
        // Handle scene expansion
        console.log('Expand scene for beat:', beatId);
      }}
    />
  );
}
```

## Keyboard Shortcuts

- `Cmd+Z` / `Ctrl+Z`: Undo
- `Cmd+Shift+Z` / `Ctrl+Shift+Z`: Redo
- `Cmd+S` / `Ctrl+S`: Save all changes immediately
- `Cmd+Enter` / `Ctrl+Enter`: Save current field (when editing)
- `Escape`: Cancel editing

## API Integration

The component uses the following API endpoints:

- `GET /stories/{storyId}/beats` - Load beats
- `PUT /beats/{beatId}` - Update a beat
- `POST /stories/{storyId}/beats` - Create a beat
- `DELETE /beats/{beatId}` - Delete a beat
- `POST /stories/{storyId}/beats/reorder` - Reorder beats

## Component Structure

- `BeatEditor.tsx` - Main editor component with drag-and-drop
- `BeatCard.tsx` - Individual beat card with inline editing
- `useBeatEditor.ts` - Custom hook for beat management logic
- `beatStore.ts` - Zustand store for state management

## Styling

Uses Tailwind CSS with a purple/indigo theme. Beats are color-coded by type:
- Hook/Opening: Blue
- Inciting Incident: Purple
- Crisis/Dark Night: Red
- Climax: Orange
- Resolution/Ending: Green
- Default: Indigo

## Environment Variables

Set `VITE_API_URL` in your `.env` file:

```
VITE_API_URL=http://localhost:8080
```

