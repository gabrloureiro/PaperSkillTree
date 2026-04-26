import React, { useCallback, useEffect, useState, useMemo } from 'react';
import ReactFlow, {
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  MarkerType,
  Handle,
  Position,
  NodeToolbar,
  ConnectionLineType
} from 'reactflow';
import * as Icons from 'lucide-react';
import 'reactflow/dist/style.css';

const CustomNode = ({ data, selected }) => {
  const IconComponent = Icons[data.iconName] || Icons.Circle;
  const isHoverMode = data.showLabels === 'hover';
  
  return (
    <div className={`custom-node ${data.isCompleted ? 'completed' : data.isUnlocked ? 'unlocked' : 'locked'} ${isHoverMode ? 'hover-mode' : ''} ${selected ? 'is-selected' : ''}`}>
      <Handle type="target" position={Position.Left} isConnectable={false} style={{ width: '8px', height: '8px' }} />
      <div className="icon-container">
        <IconComponent size={24} />
      </div>
      <div className="label-container">
        {data.label}
      </div>
      <Handle type="source" position={Position.Right} isConnectable={false} style={{ width: '8px', height: '8px' }} />
    </div>
  );
};

const GraphViewer = ({ 
  data, 
  onNodeClick, 
  completedNodes = [], 
  unlockedNodes = [], 
  selectedNodeId, 
  onClosePanel,
  showLabels = 'always'
}) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    if (!data || !data.skill_tree_nodes) return;

    // Grid layout fallback
    const rfNodes = data.skill_tree_nodes.map((node, index) => {
      const isCompleted = completedNodes.includes(node.node_id);
      const isUnlocked = unlockedNodes.includes(node.node_id);
      const isLocked = !isCompleted && !isUnlocked;
      
      return {
        id: node.node_id,
        data: { 
          label: node.concept_name,
          iconName: node.icon_name || 'Circle',
          isCompleted,
          isUnlocked,
          isLocked,
          showLabels
        },
        position: { x: (index % 5) * 250, y: Math.floor(index / 5) * 150 },
        type: 'custom',
        selected: node.node_id === selectedNodeId
      };
    });

    const rfEdges = (data.directed_acyclic_graph || []).map((edge, index) => {
      const isSourceCompleted = completedNodes.includes(edge.source);
      return {
        id: `e-${edge.source}-${edge.target}-${index}`,
        source: edge.source,
        target: edge.target,
        type: 'smoothstep', 
        animated: isSourceCompleted,
        style: { stroke: isSourceCompleted ? '#10b981' : '#9ca3af', strokeWidth: 2 },
        markerEnd: { type: MarkerType.ArrowClosed, color: isSourceCompleted ? '#10b981' : '#9ca3af' },
      };
    });

    setNodes(rfNodes);
    setEdges(rfEdges);
  }, [data, completedNodes, unlockedNodes, showLabels, selectedNodeId]);

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={{ custom: CustomNode }}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={(_, node) => onNodeClick(node.data.fullData)}
        onPaneClick={onClosePanel}
        fitView
      >
        <Controls />
        <Background />
      </ReactFlow>
    </div>
  );
};

export default GraphViewer;
