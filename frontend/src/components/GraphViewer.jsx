import React, { useCallback, useEffect, useState, useMemo } from 'react';
import ReactFlow, {
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  MarkerType,
  Handle,
  Position,
  NodeToolbar
} from 'reactflow';
import dagre from 'dagre';
import * as Icons from 'lucide-react';
import NodeSidePanel from './NodeSidePanel';
import 'reactflow/dist/style.css';

const CustomNode = ({ data, selected }) => {
  const IconComponent = Icons[data.iconName] || Icons.Circle;
  const isHoverMode = data.showLabels === 'hover';
  
  const posMap = {
    'top': Position.Top,
    'bottom': Position.Bottom,
    'right': Position.Right
  };
  const isPopover = data.panelLayout !== 'sidebar';

  return (
    <>
      {isPopover && (
        <NodeToolbar isVisible={selected} position={posMap[data.panelLayout] || Position.Top} offset={data.panelLayout === 'right' ? 30 : 60}>
          <div 
            className="node-popover-wrapper nowheel nodrag" 
            onClick={e => e.stopPropagation()}
            onMouseDown={e => e.stopPropagation()}
            onMouseUp={e => e.stopPropagation()}
            onPointerDown={e => e.stopPropagation()}
            onPointerUp={e => e.stopPropagation()}
            onTouchStart={e => e.stopPropagation()}
            onTouchEnd={e => e.stopPropagation()}
          >
            <NodeSidePanel 
              node={data.fullData} 
              treeData={data.treeData}
              treeId={data.treeId}
              onClose={data.onClosePanel}
              isUnlocked={data.isUnlocked}
              isCompleted={data.isCompleted}
              markCompleted={data.markCompleted}
              isDebugMode={data.isDebugMode}
              toggleCompleted={data.toggleCompleted}
              layout={data.panelLayout}
              tutorHistories={data.tutorHistories}
              setTutorHistories={data.setTutorHistories}
              examinerAssessments={data.examinerAssessments}
              setExaminerAssessments={data.setExaminerAssessments}
            />
          </div>
        </NodeToolbar>
      )}
      <div className={`custom-node ${data.isCompleted ? 'completed' : data.isUnlocked ? 'unlocked' : 'locked'} ${isHoverMode ? 'hover-mode' : ''} ${selected ? 'is-selected' : ''}`}>
        <Handle type="target" position={Position.Left} isConnectable={false} />
      <div className="icon-container">
        <IconComponent size={24} />
      </div>
      <div className="label-container">
        {data.label}
      </div>
        <Handle type="source" position={Position.Right} isConnectable={false} />
      </div>
    </>
  );
};

const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const nodeWidth = 200;
const nodeHeight = 60;

const getLayoutedElements = (nodes, edges, direction = 'TB') => {
  const isHorizontal = direction === 'LR';
  dagreGraph.setGraph({ rankdir: direction });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const newNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      targetPosition: isHorizontal ? 'left' : 'top',
      sourcePosition: isHorizontal ? 'right' : 'bottom',
      position: {
        x: nodeWithPosition.x - nodeWidth / 2,
        y: nodeWithPosition.y - nodeHeight / 2,
      },
    };
  });

  return { nodes: newNodes, edges };
};

const nodeTypes = {
  custom: CustomNode,
};

const GraphViewer = ({ data, onNodeClick, completedNodes = [], unlockedNodes = [], isDebugMode, setIsDebugMode, selectedNodeId, selectedNodeFullData, treeId, onClosePanel, markNodeCompleted, toggleNodeCompleted, panelLayout, setPanelLayout, tutorHistories, setTutorHistories, examinerAssessments, setExaminerAssessments }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [showLabels, setShowLabels] = useState('always'); // 'always' or 'hover'
  const [rfInstance, setRfInstance] = useState(null);

  useEffect(() => {
    if (!data) return;

    // Process nodes
    const initialNodes = (data.skill_tree_nodes || []).map((node) => {
      const isCompleted = completedNodes.includes(node.node_id);
      const isUnlocked = unlockedNodes.includes(node.node_id);
      const isLocked = !isCompleted && !isUnlocked;
      
      let background = 'var(--bg-panel)';
      let color = 'var(--text-primary)';
      let borderColor = 'var(--border-color)';

      if (isCompleted) {
        background = 'rgba(16, 185, 129, 0.2)'; // green
        borderColor = 'rgb(16, 185, 129)';
      } else if (isUnlocked) {
        background = 'rgba(59, 130, 246, 0.2)'; // blue
        borderColor = 'rgb(59, 130, 246)';
      } else if (isLocked) {
        background = 'rgba(156, 163, 175, 0.1)'; // gray
        color = 'var(--text-secondary)';
        borderColor = 'rgba(156, 163, 175, 0.3)';
      }

      return {
        id: node.node_id,
        data: { 
          label: node.concept_name,
          iconName: node.icon_name || 'Circle',
          fullData: node,
          treeData: data,
          treeId,
          isCompleted,
          isUnlocked,
          isLocked,
          showLabels,
          onClosePanel,
          markCompleted: () => markNodeCompleted(node.node_id),
          isDebugMode,
          toggleCompleted: () => toggleNodeCompleted(node.node_id),
          panelLayout,
          tutorHistories,
          setTutorHistories,
          examinerAssessments,
          setExaminerAssessments
        },
        position: { x: 0, y: 0 },
        type: 'custom',
        style: {
          cursor: 'pointer',
          opacity: isLocked ? 0.6 : 1
        }
      };
    });

    // Process edges
    const initialEdges = (data.directed_acyclic_graph || []).map((edge, index) => {
      const isSourceCompleted = completedNodes.includes(edge.source);
      
      let edgeColor = 'var(--text-secondary)';
      if (isSourceCompleted) {
        edgeColor = 'rgb(16, 185, 129)'; // green
      }
      
      return {
        id: `e-${edge.source}-${edge.target}-${index}`,
        source: edge.source,
        target: edge.target,
        type: 'smoothstep',
        animated: false,
        style: { stroke: edgeColor, strokeWidth: 2 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: edgeColor,
        },
      };
    });

    // Calculate layout
    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
      initialNodes,
      initialEdges,
      'LR' // Left to Right
    );

    setNodes((currentNodes) => {
      return layoutedNodes.map(n => {
        const existingNode = currentNodes.find(cn => cn.id === n.id);
        return {
          ...n,
          selected: existingNode ? existingNode.selected : false
        };
      });
    });
    setEdges(layoutedEdges);
  }, [data, completedNodes, unlockedNodes, showLabels, treeId, onClosePanel, markNodeCompleted, toggleNodeCompleted, isDebugMode, panelLayout, tutorHistories, examinerAssessments, setNodes, setEdges]);

  // Sync ReactFlow selection with App.jsx selectedNodeId
  useEffect(() => {
    setNodes((nds) => 
      nds.map((node) => ({
        ...node,
        selected: node.id === selectedNodeId,
      }))
    );
  }, [selectedNodeId, setNodes]);

  const handleNodeClick = useCallback(
    (_, node) => {
      onNodeClick(node.data.fullData);
      if (rfInstance) {
        let offsetX = 0;
        let offsetY = 0;
        const zoom = 1.2;
        
        if (panelLayout === 'top') {
          offsetY = -(window.innerHeight * 0.35) / zoom;
        } else if (panelLayout === 'bottom') {
          offsetY = (window.innerHeight * 0.35) / zoom;
        } else if (panelLayout === 'right') {
          offsetX = (window.innerWidth * 0.25) / zoom;
        } else if (panelLayout === 'sidebar') {
          offsetX = 0;
        }

        rfInstance.setCenter(
          node.position.x + nodeWidth / 2 + offsetX, 
          node.position.y + nodeHeight / 2 + offsetY, 
          { duration: 800, zoom }
        );
      }
    },
    [onNodeClick, rfInstance, panelLayout]
  );

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }} className="animate-fade-in">
      <div style={{ position: 'absolute', top: 20, left: 20, zIndex: 10, display: 'flex', gap: '10px' }}>
        <button 
          onClick={() => setShowLabels(prev => prev === 'always' ? 'hover' : 'always')}
          style={{ padding: '8px 16px', background: 'var(--bg-panel)', color: 'var(--text-secondary)', border: '1px solid var(--border-color)', borderRadius: '8px', cursor: 'pointer' }}
        >
          {showLabels === 'always' ? 'Hide Labels (Hover)' : 'Always Show Labels'}
        </button>
        <button 
          onClick={() => setIsDebugMode(prev => !prev)}
          style={{ padding: '8px 16px', background: isDebugMode ? 'rgba(99, 102, 241, 0.2)' : 'var(--bg-panel)', color: isDebugMode ? 'var(--accent-color)' : 'var(--text-secondary)', border: `1px solid ${isDebugMode ? 'var(--accent-color)' : 'var(--border-color)'}`, borderRadius: '8px', cursor: 'pointer' }}
        >
          Debug Mode: {isDebugMode ? 'ON' : 'OFF'}
        </button>
        <div className="layout-dropdown-wrapper">
          <select 
            value={panelLayout}
            onChange={(e) => setPanelLayout(e.target.value)}
            className="layout-select"
          >
            <option value="sidebar">Layout: Sidebar</option>
            <option value="top">Layout: Top</option>
            <option value="bottom">Layout: Bottom</option>
            <option value="right">Layout: Right</option>
          </select>
          <Icons.ChevronDown size={16} className="dropdown-icon" />
        </div>
      </div>
      <div style={{ width: panelLayout === 'sidebar' && selectedNodeId ? 'calc(100% - 400px)' : '100%', height: '100%', transition: 'width 0.3s ease' }}>
        <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        onPaneClick={onClosePanel}
        onInit={setRfInstance}
        fitView
        minZoom={0.2}
        maxZoom={1.5}
        defaultEdgeOptions={{ zIndex: 0 }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={true}
      >
        <Controls 
          style={{ background: 'var(--bg-panel)', borderColor: 'var(--border-color)', color: 'var(--text-primary)' }} 
          className="custom-controls"
        />
        <Background color="var(--border-color)" gap={20} size={1} />
        </ReactFlow>
      </div>
      {panelLayout === 'sidebar' && selectedNodeId && (
        <div style={{ position: 'absolute', top: 0, right: 0, height: '100%', width: '400px', zIndex: 50 }}>
          <NodeSidePanel 
            node={selectedNodeFullData}
            treeData={data}
            treeId={treeId}
            onClose={onClosePanel}
            isUnlocked={unlockedNodes.includes(selectedNodeId)}
            isCompleted={completedNodes.includes(selectedNodeId)}
            markCompleted={() => markNodeCompleted(selectedNodeId)}
            isDebugMode={isDebugMode}
            toggleCompleted={() => toggleNodeCompleted(selectedNodeId)}
            layout="sidebar"
            tutorHistories={tutorHistories}
            setTutorHistories={setTutorHistories}
            examinerAssessments={examinerAssessments}
            setExaminerAssessments={setExaminerAssessments}
          />
        </div>
      )}
    </div>
  );
};

export default GraphViewer;
