import React, { useState, useEffect, useRef } from 'react';
import { X, BookOpen, FileText, Send, User, GraduationCap, ClipboardCheck, CheckCircle } from 'lucide-react';
import './NodeSidePanel.css';

const NodeSidePanel = ({ node, treeData, treeId, onClose, isUnlocked, isCompleted, markCompleted, isDebugMode, toggleCompleted, layout = 'right', tutorHistories, setTutorHistories, examinerAssessments, setExaminerAssessments }) => {
  const [activeTab, setActiveTab] = useState('explanation'); // explanation, tutor, examiner
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const chatContainerRef = useRef(null);

  const tutorHistory = tutorHistories[node?.node_id] || [];
  const setTutorHistory = (historyOrUpdater) => {
    setTutorHistories(prev => ({
      ...prev,
      [node.node_id]: typeof historyOrUpdater === 'function' ? historyOrUpdater(prev[node.node_id] || []) : historyOrUpdater
    }));
  };

  const assessment = examinerAssessments[node?.node_id] || null;
  const setAssessment = (ass) => {
    setExaminerAssessments(prev => ({
      ...prev,
      [node.node_id]: ass
    }));
  };

  useEffect(() => {
    // Reset input when a new node is opened
    setActiveTab('explanation');
    setInputText('');
  }, [node]);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [tutorHistory, activeTab, assessment]);

  if (!node) return null;

  const handleSend = async () => {
    if (!inputText.trim() || isLoading) return;
    
    const userMessage = { role: 'user', content: inputText };
    
    setInputText('');
    setIsLoading(true);
    
    try {
      if (activeTab === 'tutor') {
        setTutorHistory(prev => [...prev, userMessage]);
        const res = await fetch(`http://localhost:8000/chat/tutor`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            node_id: node.node_id,
            tree_id: treeId,
            message: userMessage.content,
            chat_history: tutorHistory
          })
        });
        const data = await res.json();
        setTutorHistory(prev => [...prev, { role: 'agent', content: data.response }]);
      } else {
        const res = await fetch(`http://localhost:8000/chat/examiner`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            node_id: node.node_id,
            tree_id: treeId,
            message: userMessage.content,
            chat_history: []
          })
        });
        const data = await res.json();
        setAssessment(data);
        if (data.passed) {
          markCompleted();
        }
      }
    } catch (error) {
      console.error(error);
      if (activeTab === 'tutor') {
        setTutorHistory(prev => [...prev, { role: 'agent', content: "Sorry, I encountered an error. Please try again." }]);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const renderChat = (history) => (
    <div className="chat-container">
      <div className="chat-history" ref={chatContainerRef}>
        {history.length === 0 && (
          <p className="chat-empty">
            Ask me anything about this concept if you're confused!
          </p>
        )}
        {history.map((msg, i) => (
          <div key={i} className={`chat-message ${msg.role}`}>
            <div className="message-icon">
              {msg.role === 'user' ? <User size={16} /> : <GraduationCap size={16} />}
            </div>
            <div className="message-content">{msg.content}</div>
          </div>
        ))}
        {isLoading && <div className="chat-message agent"><div className="message-content loading-dots">...</div></div>}
      </div>
      
      <div className="chat-input-wrapper">
        <input 
          type="text" 
          value={inputText}
          onChange={e => setInputText(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          placeholder="Ask a question..."
          disabled={isLoading}
        />
        <button onClick={handleSend} disabled={!inputText.trim() || isLoading} className="send-btn">
          <Send size={16} />
        </button>
      </div>
    </div>
  );

  const renderExaminer = () => {
    if (isLoading) {
      return (
        <div className="chat-container">
          <div className="chat-message agent"><div className="message-content loading-dots">Grading your explanation...</div></div>
        </div>
      );
    }

    if (assessment) {
      const displayGrade = assessment.letter_grade || (assessment.passed ? 'A' : 'F');
      const gradeBase = displayGrade.charAt(0).toLowerCase();
      
      return (
        <div className="chat-container">
          <div className={`grade-box grade-${gradeBase}`}>
            <div className="grade-header">
              <h3 className="grade-title">{assessment.passed ? 'Excellent!' : 'Needs Work'}</h3>
              <span className="grade-badge">{displayGrade}</span>
            </div>
            <p className="grade-explanation">{assessment.response}</p>
            {!assessment.passed && (
               <button onClick={() => { setAssessment(null); setInputText(''); }} style={{marginTop: '10px', padding: '8px 16px', background: 'var(--bg-panel)', color: 'var(--text-primary)', border: '1px solid var(--border-color)', borderRadius: '6px', cursor: 'pointer', alignSelf: 'flex-start'}}>
                 Try Again
               </button>
            )}
          </div>
        </div>
      );
    }

    return (
      <div className="chat-container">
        <div className="chat-history">
          <p className="chat-empty">Explain this concept to me in your own words to pass. Be as detailed as possible!</p>
        </div>
        {!isCompleted ? (
          <div className="chat-input-wrapper">
            <input 
              type="text" 
              value={inputText} 
              onChange={e => setInputText(e.target.value)} 
              onKeyDown={e => e.key === 'Enter' && handleSend()} 
              placeholder="Type your explanation..." 
              disabled={isLoading}
            />
            <button onClick={handleSend} disabled={!inputText.trim() || isLoading} className="send-btn"><Send size={16} /></button>
          </div>
        ) : (
          <div className="completed-badge" style={{marginTop: '20px'}}>
            <CheckCircle size={20} />
            <span>You have mastered this concept!</span>
          </div>
        )}
      </div>
    );
  };

  const getConceptName = (id) => {
    if (!treeData || !treeData.skill_tree_nodes) return id;
    const n = treeData.skill_tree_nodes.find(n => n.node_id === id);
    return n ? n.concept_name : id;
  };

  const panelClass = `side-panel animate-fade-in ${layout === 'sidebar' ? 'layout-sidebar' : 'layout-popover notch-' + layout}`;

  return (
    <div className={panelClass} onClick={e => e.stopPropagation()}>
        <div className="side-panel-header">
          <div className="header-title">
            <BookOpen size={20} className="icon-accent" />
            <h3>Concept Details</h3>
          </div>
          <button className="close-btn" onClick={onClose} aria-label="Close panel">
            <X size={20} />
          </button>
        </div>

        <div className="side-panel-content">
          <h2 className="concept-title">{node.concept_name}</h2>
          
          {isDebugMode && (
            <div style={{ display: 'flex', gap: '8px', marginBottom: '15px', flexWrap: 'wrap' }}>
              <button 
                onClick={toggleCompleted} 
                style={{ flex: '1 1 100%', background: 'rgba(99, 102, 241, 0.2)', border: '1px solid var(--accent-color)', color: 'var(--accent-color)', padding: '8px', borderRadius: '6px', cursor: 'pointer', fontWeight: '500' }}
              >
                Force {isCompleted ? 'Uncomplete' : 'Complete'}
              </button>
              {['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-', 'F'].map(grade => (
                <button 
                  key={grade}
                  onClick={() => {
                    setActiveTab('examiner');
                    setAssessment({
                      passed: ['A+', 'A', 'A-', 'B+', 'B', 'B-'].includes(grade),
                      letter_grade: grade,
                      response: `This is a mocked ${grade} grade response generated by Debug Mode.`
                    });
                  }}
                  style={{ flex: '1 1 20%', background: 'var(--bg-panel)', border: '1px solid var(--border-color)', color: 'var(--text-secondary)', padding: '4px', borderRadius: '4px', cursor: 'pointer', fontSize: '0.8rem', minWidth: '40px' }}
                >
                  {grade}
                </button>
              ))}
            </div>
          )}

          <div className="metadata-section">
            <span className="metadata-label">
              <FileText size={14} /> Source Section:
            </span>
            <span className="metadata-value">{node.source_section_header || "Unknown"}</span>
          </div>

          {!isUnlocked && !isCompleted ? (
            <div className="locked-message">
              <p>🔒 Complete prerequisites first to unlock this concept.</p>
              {node.prerequisite_node_ids && node.prerequisite_node_ids.length > 0 && (
                <ul className="prereq-list">
                  {node.prerequisite_node_ids.map(id => (
                    <li key={id} className="prereq-item">{getConceptName(id)}</li>
                  ))}
                </ul>
              )}
            </div>
          ) : (
            <>
              <div className="tabs">
                <button 
                  className={`tab-btn ${activeTab === 'explanation' ? 'active' : ''}`}
                  onClick={() => setActiveTab('explanation')}
                >
                  Explanation
                </button>
                <button 
                  className={`tab-btn ${activeTab === 'tutor' ? 'active' : ''}`}
                  onClick={() => setActiveTab('tutor')}
                >
                  Tutor
                </button>
                <button 
                  className={`tab-btn ${activeTab === 'examiner' ? 'active' : ''}`}
                  onClick={() => setActiveTab('examiner')}
                >
                  Examiner {isCompleted && '✅'}
                </button>
              </div>

              <div className="tab-content">
                {activeTab === 'explanation' && (
                  <div className="explanation-section">
                    <div className="explanation-text">
                      {node.explanation.split('\n').map((paragraph, idx) => (
                        <p key={idx}>{paragraph}</p>
                      ))}
                    </div>
                  </div>
                )}

                {activeTab === 'tutor' && renderChat(tutorHistory)}
                {activeTab === 'examiner' && renderExaminer()}
              </div>
            </>
          )}
        </div>
    </div>
  );
};

export default NodeSidePanel;
