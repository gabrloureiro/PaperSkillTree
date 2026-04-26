import { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import GraphViewer from './components/GraphViewer';
import NodeSidePanel from './components/NodeSidePanel';
import { Network } from 'lucide-react';
import './App.css';

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
  const [completedNodes, setCompletedNodes] = useState(() => {
    const saved = localStorage.getItem('completedNodes');
    return saved ? JSON.parse(saved) : [];
  });

  useEffect(() => {
    localStorage.setItem('completedNodes', JSON.stringify(completedNodes));
  }, [completedNodes]);

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

  const resetProgress = useCallback(() => {
    setCompletedNodes([]);
    localStorage.removeItem('completedNodes');
  }, []);

  const fetchSkillTrees = async () => {
    try {
      const res = await fetch('http://localhost:8000/skill-trees');
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
    try {
      const res = await fetch(`http://localhost:8000/skill-trees/${treeId}`);
      if (!res.ok) throw new Error('Failed to load skill tree');
      const data = await res.json();
      setTreeData(data.tree_data);
      setSelectedTreeId(treeId);
    } catch (err) {
      console.error(err);
      setError('Failed to load the selected skill tree.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpload = async (file) => {
    setIsLoading(true);
    setError(null);
    setSelectedNode(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const res = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      });
      
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Upload failed');
      }
      const data = await res.json();
      
      setTreeData(data.tree_data);
      setSelectedTreeId('recent_upload'); // temporary ID
      fetchSkillTrees(); // Refresh list
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleDeleteTree = async (treeId) => {
    if (!window.confirm("Are you sure you want to delete this paper?")) return;
    
    try {
      const res = await fetch(`http://localhost:8000/skill-trees/${treeId}`, {
        method: 'DELETE'
      });
      if (!res.ok) throw new Error('Failed to delete skill tree');
      
      if (selectedTreeId === treeId) {
        setTreeData(null);
        setSelectedTreeId(null);
        setSelectedNode(null);
      }
      fetchSkillTrees();
    } catch (err) {
      console.error(err);
      setError('Failed to delete the paper.');
    }
  };

  const handleRenameTree = async (treeId, newTitle) => {
    try {
      const res = await fetch(`http://localhost:8000/skill-trees/${treeId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newTitle })
      });
      if (!res.ok) throw new Error('Failed to rename skill tree');
      fetchSkillTrees();
    } catch (err) {
      console.error(err);
      setError('Failed to rename the paper.');
    }
  };

  const handleNodeClick = useCallback((nodeData) => {
    setSelectedNode(nodeData);
  }, []);

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

        {isLoading && (
          <div className="empty-state">
            <div style={{ width: 40, height: 40, border: '4px solid var(--border-color)', borderTopColor: 'var(--accent-color)', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
            <h3 style={{ marginTop: 16 }}>Processing Paper...</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>This may take a few minutes as agents extract and validate concepts.</p>
          </div>
        )}

        {treeData && !isLoading && (
          <GraphViewer 
            data={treeData} 
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
          />
        )}
      </main>
      
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

export default App;
