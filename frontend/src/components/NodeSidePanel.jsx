import React, { useState, useEffect, useRef } from 'react';
import { X, BookOpen, FileText, Send, User, GraduationCap, ClipboardCheck, CheckCircle, History, ChevronRight } from 'lucide-react';
import { getGradeColorClass, isPassing } from './GradeSelector';
import './NodeSidePanel.css';

const AutoScalingTextarea = ({ value, onChange, onKeyDown, placeholder, disabled, maxRows = 8 }) => {
  const textareaRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = '38px';
      const scrollHeight = textareaRef.current.scrollHeight;
      if (value && scrollHeight > 40) {
        const newHeight = Math.min(scrollHeight, maxRows * 22);
        textareaRef.current.style.height = `${newHeight}px`;
      }
    }
  }, [value, maxRows]);

  return (
    <textarea
      ref={textareaRef}
      value={value}
      onChange={onChange}
      onKeyDown={onKeyDown}
      placeholder={placeholder}
      disabled={disabled}
      className="auto-scaling-textarea"
      rows={1}
    />
  );
};

const NodeSidePanel = ({ node, treeData, treeId, onClose, isUnlocked, isCompleted, markCompleted, isDebugMode, toggleCompleted, layout = 'right', tutorHistories, setTutorHistories, examinerAssessments, setExaminerAssessments, passingGrade }) => {
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

  let assessments = examinerAssessments[node?.node_id] || [];
  if (assessments && !Array.isArray(assessments)) {
    assessments = [assessments];
  }
  
  const [showHistory, setShowHistory] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);
  const currentAssessment = assessments.length > 0 ? assessments[assessments.length - 1] : null;

  const addAssessment = (ass) => {
    setExaminerAssessments(prev => ({
      ...prev,
      [node.node_id]: [...(prev[node.node_id] || []), { ...ass, timestamp: Date.now() }]
    }));
    setIsRetrying(false);
  };

  useEffect(() => {
    // Reset input when a new node is opened
    setActiveTab('explanation');
    setInputText('');
    setIsRetrying(false);
    setShowHistory(false);
  }, [node]);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [tutorHistory, activeTab, assessments]);

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
            chat_history: [],
            passing_grade: passingGrade
          })
        });
        const data = await res.json();
        addAssessment({ ...data, user_explanation: userMessage.content });
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
        <AutoScalingTextarea 
          value={inputText}
          onChange={e => setInputText(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
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

    if (currentAssessment && !showHistory && !isRetrying) {
      const displayGrade = currentAssessment.letter_grade || (currentAssessment.passed ? 'A' : 'F');
      const gradeColorClass = getGradeColorClass(displayGrade);
      
      return (
        <div className="chat-container">
          <div className="examiner-view">
            <div className={`grade-card large ${gradeColorClass} selected`}>
               <div className="card-letter">{displayGrade}</div>
               <div className="card-content">
                 <div className="card-header-row">
                    <h3 className="card-status-title">{currentAssessment.passed ? 'Excellent!' : 'Needs Work'}</h3>
                    <button className="history-btn" onClick={() => setShowHistory(true)}>
                      <History size={14} /> History
                    </button>
                 </div>
                 <div className="card-explanation">{currentAssessment.response}</div>
               </div>
            </div>

            <div className="user-explanation-box">
              <div className="box-label">Your Explanation:</div>
              <div className="box-content">{currentAssessment.user_explanation}</div>
            </div>
          </div>
          
          <div className="chat-input-wrapper" style={{ marginTop: 'auto', padding: '16px 0' }}>
            <button 
              onClick={() => { 
                setInputText(currentAssessment.user_explanation || ""); 
                setIsRetrying(true);
              }} 
              className="btn-primary"
              style={{ width: '100%', padding: '12px', fontSize: '0.95rem', fontWeight: '600' }}
            >
              Try Again
            </button>
          </div>
        </div>
      );
    }

    if (showHistory) {
      return (
        <div className="chat-container">
          <div className="history-view animate-fade-in">
            <div className="history-header">
              <button className="back-btn" onClick={() => setShowHistory(false)}>
                <ChevronRight size={18} style={{ transform: 'rotate(180deg)' }} /> Back
              </button>
              <h3>Previous Attempts</h3>
            </div>
            <div className="history-list">
              {[...assessments].reverse().map((ass, idx) => {
                const grade = ass.letter_grade || (ass.passed ? 'A' : 'F');
                const colorClass = getGradeColorClass(grade);
                return (
                  <div key={idx} className={`history-card ${colorClass}`}>
                    <div className="history-user-text">{ass.user_explanation}</div>
                    <div className="history-grade">{grade}</div>
                  </div>
                );
              })}
            </div>
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
            <AutoScalingTextarea 
              value={inputText} 
              onChange={e => setInputText(e.target.value)} 
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }} 
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
              {['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-', 'F'].map(grade => {
                const passed = isPassing(grade, passingGrade);
                return (
                  <button 
                    key={grade}
                    onClick={() => {
                      setActiveTab('examiner');
                      addAssessment({
                        passed,
                        letter_grade: grade,
                        response: `This is a mocked ${grade} grade response generated by Debug Mode.`,
                        user_explanation: "This is a mock explanation for debug purposes."
                      });
                      if (passed) markCompleted();
                    }}
                    style={{ flex: '1 1 20%', background: 'var(--bg-panel)', border: passed ? '1px solid #10b981' : '1px solid var(--border-color)', color: passed ? '#10b981' : 'var(--text-secondary)', padding: '4px', borderRadius: '4px', cursor: 'pointer', fontSize: '0.8rem', minWidth: '40px' }}
                  >
                    {grade}
                  </button>
                );
              })}
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
