/**
 * Example usage of BeatEditor component
 * 
 * This file demonstrates how to use the BeatEditor component
 * in your application.
 */

import React from 'react';
import { BeatEditor } from './BeatEditor';

export function BeatEditorExample() {
  const storyId = 1; // Replace with actual story ID

  const handleExpandScene = (beatId: number) => {
    console.log('Expanding scene for beat:', beatId);
    // Navigate to scene expansion page or open modal
    // Example: navigate(`/stories/${storyId}/beats/${beatId}/expand`);
  };

  return (
    <div className="min-h-screen bg-gray-900 p-8">
      <BeatEditor 
        storyId={storyId}
        onExpandScene={handleExpandScene}
      />
    </div>
  );
}

/**
 * Example with React Router integration:
 * 
 * import { useParams } from 'react-router-dom';
 * 
 * export function StoryOutlinePage() {
 *   const { storyId } = useParams<{ storyId: string }>();
 *   
 *   return (
 *     <BeatEditor 
 *       storyId={parseInt(storyId || '0')}
 *       onExpandScene={(beatId) => {
 *         navigate(`/stories/${storyId}/beats/${beatId}/expand`);
 *       }}
 *     />
 *   );
 * }
 */

