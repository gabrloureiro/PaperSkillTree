import React, { useRef, useState } from 'react';
import { Upload, FileText, Database, Trash2, Edit2, Check, X } from 'lucide-react';
import './Sidebar.css';

const Sidebar = ({ skillTrees, onSelectTree, onUpload, onDeleteTree, onRenameTree, selectedTreeId, isLoading }) => {
  const fileInputRef = useRef(null);
  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState("");

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

  const startEditing = (e, tree) => {
    e.stopPropagation();
    setEditingId(tree.id);
    setEditValue(tree.title);
  };

  const cancelEditing = (e) => {
    e.stopPropagation();
    setEditingId(null);
    setEditValue("");
  };

  const saveRename = (e, treeId) => {
    e.stopPropagation();
    if (editValue.trim() && editValue !== skillTrees.find(t => t.id === treeId)?.title) {
      onRenameTree(treeId, editValue);
    }
    setEditingId(null);
  };

  const handleDelete = (e, treeId) => {
    e.stopPropagation();
    onDeleteTree(treeId);
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
            {skillTrees.map((tree) => (
              <li key={tree.id} className="tree-item-container">
                {editingId === tree.id ? (
                  <div className="rename-input-container">
                    <input 
                      type="text" 
                      value={editValue} 
                      onChange={(e) => setEditValue(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') saveRename(e, tree.id);
                        if (e.key === 'Escape') cancelEditing(e);
                      }}
                      autoFocus
                      className="rename-input"
                    />
                    <div className="rename-actions">
                      <button onClick={(e) => saveRename(e, tree.id)} className="icon-btn success"><Check size={14} /></button>
                      <button onClick={cancelEditing} className="icon-btn danger"><X size={14} /></button>
                    </div>
                  </div>
                ) : (
                  <div className={`tree-item-wrapper ${selectedTreeId === tree.id ? 'selected' : ''}`}>
                    <button
                      className="tree-item"
                      onClick={() => onSelectTree(tree.id)}
                      title={tree.title}
                    >
                      <FileText size={16} className="tree-item-icon" />
                      <span className="tree-item-name">{tree.title}</span>
                    </button>
                    <div className="tree-item-actions">
                      <button onClick={(e) => startEditing(e, tree)} className="icon-btn edit" title="Rename"><Edit2 size={14} /></button>
                      <button onClick={(e) => handleDelete(e, tree.id)} className="icon-btn delete" title="Delete"><Trash2 size={14} /></button>
                    </div>
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default Sidebar;
