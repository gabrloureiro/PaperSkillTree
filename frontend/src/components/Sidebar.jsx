import React, { useRef } from 'react';
import { Upload, FileText, Database } from 'lucide-react';
import './Sidebar.css';

const Sidebar = ({ skillTrees, onSelectTree, onUpload, selectedTreeId, isLoading }) => {
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file && file.type === 'application/pdf') {
      onUpload(file);
    } else {
      alert("Please select a PDF file.");
    }
    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="sidebar glass-panel">
      <div className="sidebar-header">
        <Database className="sidebar-icon" />
        <h2>Skill Trees</h2>
      </div>

      <div className="upload-section">
        <input 
          type="file" 
          accept=".pdf" 
          style={{ display: 'none' }} 
          ref={fileInputRef}
          onChange={handleFileChange}
        />
        <button 
          className="btn-primary w-100" 
          onClick={() => fileInputRef.current.click()}
          disabled={isLoading}
        >
          <Upload size={18} />
          {isLoading ? 'Processing...' : 'Upload PDF'}
        </button>
      </div>

      <div className="tree-list-container">
        <h3 className="list-title">Cached Papers</h3>
        {skillTrees.length === 0 ? (
          <p className="empty-list">No cached papers found.</p>
        ) : (
          <ul className="tree-list">
            {skillTrees.map((treeId) => (
              <li key={treeId}>
                <button
                  className={`tree-item ${selectedTreeId === treeId ? 'selected' : ''}`}
                  onClick={() => onSelectTree(treeId)}
                  title={treeId}
                >
                  <FileText size={16} className="tree-item-icon" />
                  <span className="tree-item-name">{treeId.substring(0, 12)}...</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default Sidebar;
