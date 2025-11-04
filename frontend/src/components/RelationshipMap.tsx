import React, { useState, useEffect } from 'react';
import { Network, Loader2 } from 'lucide-react';
import { characterApi } from '../lib/characterApi';
import type { Character, Relationship } from '../types/character';

interface RelationshipMapProps {
  storyId: number;
}

interface Node {
  id: number;
  name: string;
  role: string;
  x?: number;
  y?: number;
}

interface Edge {
  source: number;
  target: number;
  type: string;
  strength: number;
}

export function RelationshipMap({ storyId }: RelationshipMapProps) {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  useEffect(() => {
    loadGraph();
  }, [storyId]);

  const loadGraph = async () => {
    setLoading(true);
    try {
      const response = await characterApi.getStoryCharacters(storyId);
      const characters = response.characters;

      // Create nodes
      const nodeMap = new Map<number, Node>();
      characters.forEach((char, index) => {
        // Simple circular layout
        const angle = (2 * Math.PI * index) / characters.length;
        const radius = 150;
        nodeMap.set(char.id, {
          id: char.id,
          name: char.name,
          role: char.role,
          x: 250 + radius * Math.cos(angle),
          y: 250 + radius * Math.sin(angle),
        });
      });

      // Load relationships
      const edgeMap = new Map<string, Edge>();
      for (const char of characters) {
        try {
          const charDetail = await characterApi.getCharacter(char.id);
          if (charDetail.relationships) {
            charDetail.relationships.forEach((rel: Relationship) => {
              const key = [char.id, rel.character_id].sort().join('-');
              if (!edgeMap.has(key)) {
                edgeMap.set(key, {
                  source: char.id,
                  target: rel.character_id,
                  type: rel.type,
                  strength: rel.strength,
                });
              }
            });
          }
        } catch (err) {
          console.error(`Failed to load relationships for character ${char.id}:`, err);
        }
      }

      setNodes(Array.from(nodeMap.values()));
      setEdges(Array.from(edgeMap.values()));
    } catch (err) {
      console.error('Failed to load relationship map:', err);
    } finally {
      setLoading(false);
    }
  };

  const getRelationshipColor = (type: string): string => {
    const colors: Record<string, string> = {
      family: '#ef4444', // red
      friend: '#3b82f6', // blue
      enemy: '#dc2626', // dark red
      romance: '#ec4899', // pink
      mentor: '#8b5cf6', // purple
      rival: '#f59e0b', // amber
      ally: '#10b981', // green
      other: '#6b7280', // gray
    };
    return colors[type] || colors.other;
  };

  const getRoleColor = (role: string): string => {
    const colors: Record<string, string> = {
      protagonist: '#3b82f6',
      antagonist: '#ef4444',
      supporting: '#a855f7',
      minor: '#6b7280',
    };
    return colors[role] || colors.minor;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8 bg-gray-800 rounded-lg border border-gray-700">
        <Loader2 className="w-6 h-6 animate-spin text-indigo-400" />
      </div>
    );
  }

  if (nodes.length === 0) {
    return (
      <div className="p-8 bg-gray-800 rounded-lg border border-gray-700 text-center text-gray-400">
        <Network className="w-12 h-12 mx-auto mb-3 opacity-50" />
        <p>No characters to display. Create characters to see relationships.</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center gap-2 mb-4">
        <Network className="w-5 h-5 text-indigo-400" />
        <h3 className="text-lg font-semibold text-white">Character Relationship Map</h3>
      </div>

      <div className="relative bg-gray-900 rounded-lg border border-gray-700 overflow-hidden" style={{ height: '500px' }}>
        <svg width="100%" height="100%" className="absolute inset-0">
          {/* Render edges */}
          {edges.map((edge, idx) => {
            const sourceNode = nodes.find(n => n.id === edge.source);
            const targetNode = nodes.find(n => n.id === edge.target);
            
            if (!sourceNode || !targetNode || !sourceNode.x || !sourceNode.y || !targetNode.x || !targetNode.y) {
              return null;
            }

            return (
              <line
                key={idx}
                x1={sourceNode.x}
                y1={sourceNode.y}
                x2={targetNode.x}
                y2={targetNode.y}
                stroke={getRelationshipColor(edge.type)}
                strokeWidth={edge.strength / 2}
                opacity={0.6}
                strokeDasharray={edge.type === 'enemy' ? '5,5' : '0'}
              />
            );
          })}

          {/* Render nodes */}
          {nodes.map((node) => {
            if (!node.x || !node.y) return null;

            return (
              <g
                key={node.id}
                className="cursor-pointer"
                onClick={() => setSelectedNode(node)}
              >
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={selectedNode?.id === node.id ? 25 : 20}
                  fill={getRoleColor(node.role)}
                  stroke={selectedNode?.id === node.id ? '#ffffff' : '#374151'}
                  strokeWidth={selectedNode?.id === node.id ? 3 : 2}
                  className="transition-all"
                />
                <text
                  x={node.x}
                  y={node.y + 35}
                  textAnchor="middle"
                  fill="#ffffff"
                  fontSize="12"
                  fontWeight="500"
                  className="pointer-events-none"
                >
                  {node.name}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {selectedNode && (
        <div className="mt-4 p-4 bg-gray-700 rounded-lg">
          <h4 className="font-semibold text-white mb-2">{selectedNode.name}</h4>
          <p className="text-sm text-gray-300">Role: <span className="capitalize">{selectedNode.role}</span></p>
          <button
            onClick={() => setSelectedNode(null)}
            className="mt-2 text-xs text-gray-400 hover:text-white"
          >
            Close
          </button>
        </div>
      )}

      <div className="mt-4 flex flex-wrap gap-4 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-blue-500"></div>
          <span className="text-gray-400">Friend</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500"></div>
          <span className="text-gray-400">Enemy</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-pink-500"></div>
          <span className="text-gray-400">Romance</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-purple-500"></div>
          <span className="text-gray-400">Mentor</span>
        </div>
      </div>
    </div>
  );
}
