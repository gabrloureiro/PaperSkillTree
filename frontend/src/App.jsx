import { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import GraphViewer from './components/GraphViewer';
import NodeSidePanel from './components/NodeSidePanel';
import ProcessingLog from './components/ProcessingLog';
import { Network } from 'lucide-react';
import './App.css';

const API_URL = 'http://localhost:8000';

function App() {
  const [skillTrees, setSkillTrees] = useState([]);
  const [selectedTreeId, setSelectedTreeId] = useState(null);
  const [treeData, setTreeData] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isDebugMode, setIsDebugMode] = useState(false);
  const [panelLayout, setPanelLayout] = useState('right'); // sidebar, top, right, bottom
  const [tutorHistories, setTutorHistories] = useState({});
  const [examinerAssessments, setExaminerAssessments] = useState({});
  const [completedNodes, setCompletedNodes] = useState([]);
  const [passingGrade, setPassingGrade] = useState({}); // { [treeId]: grade }

  useEffect(() => {
    const savedCompleted = localStorage.getItem('completedNodes');
    if (savedCompleted) setCompletedNodes(JSON.parse(savedCompleted));
    
    const savedTutor = localStorage.getItem('tutorHistories');
    if (savedTutor) setTutorHistories(JSON.parse(savedTutor));
    
    const savedExaminer = localStorage.getItem('examinerAssessments');
    if (savedExaminer) setExaminerAssessments(JSON.parse(savedExaminer));
    
    const savedPassing = localStorage.getItem('passingGrades');
    if (savedPassing) setPassingGrade(JSON.parse(savedPassing));
  }, []);

  useEffect(() => {
    localStorage.setItem('completedNodes', JSON.stringify(completedNodes));
  }, [completedNodes]);

  useEffect(() => {
    localStorage.setItem('tutorHistories', JSON.stringify(tutorHistories));
  }, [tutorHistories]);

  useEffect(() => {
    localStorage.setItem('examinerAssessments', JSON.stringify(examinerAssessments));
  }, [examinerAssessments]);

  useEffect(() => {
    localStorage.setItem('passingGrades', JSON.stringify(passingGrade));
  }, [passingGrade]);

  const markNodeCompleted = useCallback((nodeId) => {
    setCompletedNodes(prev => {
      if (prev.includes(nodeId)) return prev;
      return [...prev, nodeId];
    });
  }, []);

  const toggleNodeCompleted = useCallback((nodeId) => {
    setCompletedNodes(prev => {
      if (prev.includes(nodeId)) return prev.filter(id => id !== nodeId);
      return [...prev, nodeId];
    });
  }, []);

  const resetProgress = useCallback(async () => {
    if (!selectedTreeId) return;
    if (window.confirm("Are you sure you want to reset all progress for this paper? This will clear all completed nodes, chat histories, and reset the passing grade.")) {
      try {
        await fetch(`${API_URL}/skill-trees/${selectedTreeId}/reset`, {
          method: 'POST'
        });
        
        setCompletedNodes([]);
        
        setTutorHistories(prev => {
          const next = { ...prev };
          if (treeData?.skill_tree_nodes) {
            treeData.skill_tree_nodes.forEach(node => {
              delete next[node.node_id];
            });
          }
          return next;
        });

        setExaminerAssessments(prev => {
          const next = { ...prev };
          if (treeData?.skill_tree_nodes) {
            treeData.skill_tree_nodes.forEach(node => {
              delete next[node.node_id];
            });
          }
          return next;
        });

        setPassingGrade(prev => ({ ...prev, [selectedTreeId]: "B-" }));
        
        localStorage.removeItem('completedNodes');
      } catch (err) {
        console.error("Failed to reset progress on backend:", err);
        setError("Failed to reset progress on the server.");
      }
    }
  }, [selectedTreeId, treeData]);

  const fetchSkillTrees = async () => {
    try {
      const res = await fetch(`${API_URL}/skill-trees`);
      if (!res.ok) throw new Error('Failed to fetch skill trees');
      const data = await res.json();
      setSkillTrees(data.skill_trees || []);
    } catch (err) {
      console.error(err);
      setError('Could not connect to backend.');
    }
  };

  useEffect(() => {
    fetchSkillTrees();
  }, []);

  const loadSkillTree = async (treeId) => {
    setIsLoading(true);
    setError(null);
    setSelectedNode(null);
    setTreeData(null);
    setStreamingTreeData(null);
    setProcessingEvents([]);
    setSelectedTreeId(treeId);
    try {
      const res = await fetch(`${API_URL}/skill-trees/${treeId}`);
      if (!res.ok) throw new Error('Failed to load skill tree');
      const data = await res.json();
      const loadedTreeData = data.tree_data;
      setTreeData(loadedTreeData);
      
      // Pull passing grade from backend if available
      if (loadedTreeData.metadata?.passing_grade) {
        setPassingGrade(prev => ({ ...prev, [treeId]: loadedTreeData.metadata.passing_grade }));
      }
      
      // Sync completed nodes from backend
      if (loadedTreeData.skill_tree_nodes) {
        const backendCompleted = loadedTreeData.skill_tree_nodes
          .filter(n => n.completed)
          .map(n => n.node_id);
        
        setCompletedNodes(prev => {
          const combined = new Set([...prev, ...backendCompleted]);
          return Array.from(combined);
        });
      }
    } catch (err) {
      console.error(err);
      setError('Failed to load the selected skill tree.');
    } finally {
      setIsLoading(false);
    }
  };

  const [isComplexityModalOpen, setIsComplexityModalOpen] = useState(false);
  const [pendingFile, setPendingFile] = useState(null);
  const [selectedComplexity, setSelectedComplexity] = useState('simple');

  const handleUpload = (file) => {
    setPendingFile(file);
    setIsComplexityModalOpen(true);
  };

  const [processingEvents, setProcessingEvents] = useState([]);
  const [streamingTreeData, setStreamingTreeData] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleStreamEvent = useCallback((event) => {
    if (event.type === 'agent_start') {
      setProcessingEvents(prev => [...prev, { type: 'start', agent: event.agent, timestamp: Date.now() }]);
    } else if (event.type === 'agent_stop') {
      // Could handle stop if needed, but start/message is usually enough
    } else if (event.type === 'agent_message') {
      setProcessingEvents(prev => [...prev, { type: 'message', agent: event.agent, content: event.content, timestamp: Date.now() }]);
    } else if (event.type === 'skeleton_discovered') {
      setStreamingTreeData({
        skill_tree_nodes: event.nodes.map(n => ({ ...n, isSkeleton: true })),
        directed_acyclic_graph: event.edges
      });
    } else if (event.type === 'node_finalized') {
      setStreamingTreeData(prev => {
        if (!prev) return prev;
        const existingNode = prev.skill_tree_nodes.find(n => n.node_id === event.node.node_id);
        let newNodes;
        if (existingNode) {
          newNodes = prev.skill_tree_nodes.map(n => 
            n.node_id === event.node.node_id ? { ...event.node, isSkeleton: false } : n
          );
        } else {
          newNodes = [...prev.skill_tree_nodes, { ...event.node, isSkeleton: false }];
        }
        return { ...prev, skill_tree_nodes: newNodes };
      });
    } else if (event.type === 'graph_synthesized') {
      setStreamingTreeData(prev => ({
        ...prev,
        directed_acyclic_graph: event.edges,
        skill_tree_nodes: (event.nodes || prev.skill_tree_nodes).map(n => ({ ...n, isSkeleton: false }))
      }));
    } else if (event.type === 'final_result') {
      setTreeData(event.data);
      // Wait a bit before turning off processing for smooth transition
      setTimeout(() => {
        setIsProcessing(false);
        setIsLoading(false);
      }, 1000);
    } else if (event.type === 'complete') {
      if (event.tree_id) setSelectedTreeId(event.tree_id);
      fetchSkillTrees();
    } else if (event.type === 'error') {
      setError(event.detail);
      setIsProcessing(false);
      setIsLoading(false);
    }
  }, [fetchSkillTrees]);

  const confirmUpload = async () => {
    if (!pendingFile) return;
    
    const file = pendingFile;
    const complexity = selectedComplexity;
    
    setIsComplexityModalOpen(false);
    setPendingFile(null);
    setIsLoading(true);
    setIsProcessing(true);
    setProcessingEvents([]);
    setStreamingTreeData(null);
    setTreeData(null);
    setError(null);
    setSelectedNode(null);
    setSelectedTreeId(null);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch(`${API_URL}/upload-stream?complexity=${complexity}`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) throw new Error('Upload failed');
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop(); // Keep incomplete line in buffer
        
        for (const part of parts) {
          if (part.startsWith('data: ')) {
            try {
              const data = JSON.parse(part.slice(6));
              handleStreamEvent(data);
            } catch (e) {
              console.error("Failed to parse stream event:", e, part);
            }
          }
        }
      }
    } catch (err) {
      console.error(err);
      setError('Failed to upload and process PDF.');
      setIsLoading(false);
      setIsProcessing(false);
    }
  };

  const handleNodeClick = useCallback((nodeData) => {
    setSelectedNode(nodeData);
  }, []);

  const handleRenameTree = async (treeId, newTitle) => {
    try {
      const res = await fetch(`${API_URL}/skill-trees/${treeId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newTitle }),
      });
      if (!res.ok) throw new Error('Failed to rename skill tree');
      fetchSkillTrees(); // Refresh list
    } catch (err) {
      console.error(err);
      setError('Failed to rename paper.');
    }
  };

  const handleDeleteTree = async (treeId) => {
    if (!window.confirm('Are you sure you want to delete this paper?')) return;
    try {
      const res = await fetch(`${API_URL}/skill-trees/${treeId}`, {
        method: 'DELETE',
      });
      if (!res.ok) throw new Error('Failed to delete skill tree');
      if (selectedTreeId === treeId) {
        setTreeData(null);
        setSelectedTreeId(null);
        setSelectedNode(null);
      }
      fetchSkillTrees(); // Refresh list
    } catch (err) {
      console.error(err);
      setError('Failed to delete paper.');
    }
  };

  const handleClosePanel = useCallback(() => {
    setSelectedNode(null);
  }, []);

  const unlockedNodes = treeData?.skill_tree_nodes?.filter(node => 
    !node.prerequisite_node_ids || 
    node.prerequisite_node_ids.length === 0 || 
    node.prerequisite_node_ids.every(id => completedNodes.includes(id))
  ).map(node => node.node_id) || [];

  return (
    <div className="app-container bg-dark text-primary">
      <Sidebar 
        skillTrees={skillTrees} 
        onSelectTree={loadSkillTree}
        onUpload={handleUpload}
        onDeleteTree={handleDeleteTree}
        onRenameTree={handleRenameTree}
        selectedTreeId={selectedTreeId}
        isLoading={isLoading}
      />
      
      <main className="main-content">
        <div style={{ position: 'absolute', top: 20, right: (panelLayout === 'sidebar' && selectedNode) ? 420 : 20, zIndex: 10, transition: 'right 0.3s ease' }}>
          <button 
            onClick={resetProgress}
            style={{ padding: '8px 16px', background: 'var(--bg-panel)', color: 'var(--text-secondary)', border: '1px solid var(--border-color)', borderRadius: '8px', cursor: 'pointer' }}
          >
            Reset Progress
          </button>
        </div>
        {error && (
          <div style={{ position: 'absolute', top: 20, left: '50%', transform: 'translateX(-50%)', zIndex: 50, background: '#ef4444', color: 'white', padding: '8px 16px', borderRadius: 8 }}>
            {error}
          </div>
        )}

        {!treeData && !isLoading && (
          <div className="empty-state animate-fade-in">
            <Network className="empty-icon" />
            <h2>Paper Skill Tree Visualizer</h2>
            <p>Upload a research paper PDF or select an existing one from the sidebar to visualize its concept dependencies.</p>
          </div>
        )}

        {isLoading && !isProcessing && (
          <div className="empty-state">
            <div style={{ width: 40, height: 40, border: '4px solid var(--border-color)', borderTopColor: 'var(--accent-color)', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
            <h3 style={{ marginTop: 16 }}>Loading Skill Tree...</h3>
          </div>
        )}

        {(treeData || isProcessing) && (
          <div className="main-content-layout">
            <div className="graph-container-wrapper" style={{ width: (panelLayout === 'sidebar' && selectedNode) || isProcessing ? 'calc(100% - 400px)' : '100%' }}>
              <GraphViewer 
                data={isProcessing ? streamingTreeData : treeData} 
                onNodeClick={handleNodeClick} 
                completedNodes={completedNodes}
                unlockedNodes={unlockedNodes}
                isDebugMode={isDebugMode}
                setIsDebugMode={setIsDebugMode}
                selectedNodeId={selectedNode?.node_id}
                selectedNodeFullData={selectedNode}
                treeId={selectedTreeId}
                onClosePanel={handleClosePanel}
                markNodeCompleted={markNodeCompleted}
                toggleNodeCompleted={toggleNodeCompleted}
                panelLayout={panelLayout}
                setPanelLayout={setPanelLayout}
                tutorHistories={tutorHistories}
                setTutorHistories={setTutorHistories}
                examinerAssessments={examinerAssessments}
                setExaminerAssessments={setExaminerAssessments}
                passingGrade={passingGrade[selectedTreeId] || "B-"}
                setPassingGrade={async (grade) => {
                  setPassingGrade(prev => ({ ...prev, [selectedTreeId]: grade }));
                  // Sync with backend
                  try {
                    await fetch(`${API_URL}/skill-trees/${selectedTreeId}`, {
                      method: 'PATCH',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ passing_grade: grade }),
                    });
                  } catch (error) {
                    console.error("Failed to sync passing grade to backend:", error);
                  }
                }}
              />
            </div>
            
            {isProcessing && (
              <ProcessingLog events={processingEvents} isProcessing={isProcessing} />
            )}
            
            {panelLayout === 'sidebar' && selectedNodeId && !isProcessing && (
              <div className="side-panel-wrapper">
                <NodeSidePanel
                  node={selectedNode}
                  treeData={treeData}
                  treeId={selectedTreeId}
                  onClose={handleClosePanel}
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
                  passingGrade={passingGrade[selectedTreeId] || "B-"}
                />
              </div>
            )}
          </div>
        )}
      </main>
      
      {isComplexityModalOpen && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h2>How deeply would you like to understand the paper?</h2>
            <div className="complexity-options">
              <div 
                className={`complexity-option ${selectedComplexity === 'simple' ? 'selected' : ''}`}
                onClick={() => setSelectedComplexity('simple')}
              >
                <h3>Simple Option</h3>
                <p>Understand the core arguments, reasoning, and main takeaways. Ideal for a quick but solid overview.</p>
              </div>
              <div 
                className={`complexity-option ${selectedComplexity === 'complex' ? 'selected' : ''}`}
                onClick={() => setSelectedComplexity('complex')}
              >
                <h3>Deep Understanding</h3>
                <p>Completely teach everything in the paper. Includes models, formulas, nuances, and background knowledge.</p>
              </div>
            </div>
            <div className="modal-actions">
              <button 
                className="btn-secondary" 
                onClick={() => setIsComplexityModalOpen(false)}
                style={{ padding: '8px 20px', background: 'transparent', border: '1px solid var(--border-color)', borderRadius: '8px', cursor: 'pointer' }}
              >
                Cancel
              </button>
              <button 
                className="btn-primary" 
                onClick={confirmUpload}
                style={{ padding: '8px 24px', background: 'var(--accent-color)', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}
              >
                Generate Skill Tree
              </button>
            </div>
          </div>
        </div>
      )}

      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

export default App;
