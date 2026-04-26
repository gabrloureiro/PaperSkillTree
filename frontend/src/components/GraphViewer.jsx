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
  BaseEdge
} from 'reactflow';
import ELK from 'elkjs/lib/elk.bundled.js';
import * as Icons from 'lucide-react';
import NodeSidePanel from './NodeSidePanel';
import 'reactflow/dist/style.css';

const elk = new ELK();

const ElkEdge = ({ id, data, style, markerEnd }) => {
  if (!data?.points || data.points.length === 0) return null;
  const path = data.points.reduce(
    (acc, pt, i) => `${acc} ${i === 0 ? 'M' : 'L'} ${pt.x} ${pt.y}`,
    ''
  );
  return <BaseEdge id={id} path={path} style={style} markerEnd={markerEnd} />;
};

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

const nodeWidth = 60;
const nodeHeight = 60;

const calculateAlapLayers = (nodes, edges) => {
  const outEdges = {};
  nodes.forEach((n) => { outEdges[n.id] = []; });
  edges.forEach((e) => { outEdges[e.source].push(e.target); });

  const memo = {};

  // DFS to find the longest path from a node to any sink
  const getLongestPath = (nodeId) => {
    if (memo[nodeId] !== undefined) return memo[nodeId];
    if (outEdges[nodeId].length === 0) return 0;

    let maxPath = 0;
    for (const target of outEdges[nodeId]) {
      maxPath = Math.max(maxPath, 1 + getLongestPath(target));
    }

    memo[nodeId] = maxPath;
    return maxPath;
  };

  nodes.forEach((n) => getLongestPath(n.id));

  // The maximum path length dictates the total number of columns
  const maxGraphPath = Math.max(...Object.values(memo), 0);

  // Layer = max depth minus the node's longest path to the end
  const nodeLayers = {};
  nodes.forEach((n) => {
    nodeLayers[n.id] = maxGraphPath - (memo[n.id] || 0);
  });

  return nodeLayers;
};

const getLayoutedElements = async (nodes, edges, direction = 'RIGHT') => {
  const layers = calculateAlapLayers(nodes, edges);

  const graph = {
    id: 'root',
    layoutOptions: {
      'elk.algorithm': 'layered',
      'elk.direction': direction,
      'elk.edgeRouting': 'POLYLINE',
      'elk.portConstraints': 'FIXED_SIDE',
      // Force ELK to respect our exact ALAP layer calculations
      'elk.layered.layering.strategy': 'INTERACTIVE',
      'elk.layered.crossingMinimization.strategy': 'LAYER_SWEEP',
      'elk.layered.portRouting': 'DISTRIBUTED',
      'elk.layered.spacing.edgeNodeBetweenLayers': '50',
      'elk.spacing.edgeEdge': '20',
      'elk.spacing.nodeNode': '100',
      'elk.layered.spacing.nodeNodeBetweenLayers': '160',
      'elk.padding': '[top=50,left=50,bottom=50,right=50]'
    },
    children: nodes.map((node) => ({
      id: node.id,
      width: nodeWidth,
      height: nodeHeight,
      layoutOptions: {
        // Inject the calculated layer as a string
        'elk.layered.layer': Number(layers[node.id])
      }
    })),
    edges: edges.map((edge) => ({
      id: edge.id,
      sources: [edge.source],
      targets: [edge.target],
    })),
  };

  const layout = await elk.layout(graph);

  const layoutedNodes = nodes.map((node) => {
    const elkNode = layout.children.find((n) => n.id === node.id);
    return {
      ...node,
      targetPosition: direction === 'DOWN' ? Position.Top : Position.Left,
      sourcePosition: direction === 'DOWN' ? Position.Bottom : Position.Right,
      position: { x: elkNode.x, y: elkNode.y },
    };
  });

  const layoutedEdges = edges.map((edge) => {
    const elkEdge = layout.edges.find((e) => e.id === edge.id);
    let points = [];

    if (elkEdge?.sections) {
      elkEdge.sections.forEach((section) => {
        points.push(section.startPoint);
        if (section.bendPoints) points.push(...section.bendPoints);
        points.push(section.endPoint);
      });
    }

    // Add a small visual gap (offset) between the node and the edge start/end
    const gap = 10;
    if (points.length >= 2) {
      // Shorten the start of the edge
      const p0 = points[0];
      const p1 = points[1];
      const dx0 = p1.x - p0.x;
      const dy0 = p1.y - p0.y;
      const len0 = Math.sqrt(dx0 * dx0 + dy0 * dy0);
      if (len0 > gap) {
        points[0] = { x: p0.x + (dx0 / len0) * gap, y: p0.y + (dy0 / len0) * gap };
      }

      // Shorten the end of the edge
      const pn = points[points.length - 1];
      const pn_1 = points[points.length - 2];
      const dxn = pn_1.x - pn.x;
      const dyn = pn_1.y - pn.y;
      const lenn = Math.sqrt(dxn * dxn + dyn * dyn);
      if (lenn > gap) {
        points[points.length - 1] = { x: pn.x + (dxn / lenn) * gap, y: pn.y + (dyn / lenn) * gap };
      }
    }

    return {
      ...edge,
      type: 'elk',
      data: { ...edge.data, points },
    };
  });

  return { nodes: layoutedNodes, edges: layoutedEdges };
};

const nodeTypes = {
  custom: CustomNode,
};

const edgeTypes = {
  elk: ElkEdge,
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
        type: 'elk',
        animated: false,
        style: { stroke: edgeColor, strokeWidth: 2 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: edgeColor,
        },
      };
    });

    // Calculate layout asynchronously
    getLayoutedElements(initialNodes, initialEdges).then(({ nodes: layoutedNodes, edges: layoutedEdges }) => {
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
    });
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
          edgeTypes={edgeTypes}
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
