import React, { useState, useRef, useEffect } from 'react';
import { Award, ChevronDown, Check, X } from 'lucide-react';
import { createPortal } from 'react-dom';
import './GradeSelector.css';

export const GRADES = [
  { value: 'A+', label: 'A+', description: "You want to know this paper better than you know your family" },
  { value: 'A', label: 'A', description: "You're basically the author at this point" },
  { value: 'A-', label: 'A-', description: "You've got a PhD in this specific node" },
  { value: 'B+', label: 'B+', description: "You're the smartest kid in the class" },
  { value: 'B', label: 'B', description: "You've been paying attention" },
  { value: 'B-', label: 'B-', description: "You've got the gist of it" },
  { value: 'C+', label: 'C+', description: "You're getting the hang of it, slowly" },
  { value: 'C', label: 'C', description: "Average Joe's understanding" },
  { value: 'C-', label: 'C-', description: "You skimmed it, didn't you?" },
  { value: 'D+', label: 'D+', description: "A bit more than a guess" },
  { value: 'D', label: 'D', description: "You've heard of these words before" },
  { value: 'D-', label: 'D-', description: "You're just here for the ride" }
];

export const isPassing = (grade, threshold) => {
  const gradeIdx = GRADES.findIndex(g => g.value === grade);
  const thresholdIdx = GRADES.findIndex(g => g.value === threshold);
  if (gradeIdx === -1 || thresholdIdx === -1) return false;
  return gradeIdx <= thresholdIdx; // Lower index is better grade
};

export const getGradeColorClass = (grade) => {
  if (!grade) return 'grade-f';
  const char = grade.charAt(0).toUpperCase();
  switch (char) {
    case 'A': return 'grade-a';
    case 'B': return 'grade-b';
    case 'C': return 'grade-c';
    case 'D': return 'grade-d';
    default: return 'grade-f';
  }
};

const GradeSelector = ({ selectedGrade, onSelect }) => {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'hidden'; // Keep global hidden
    }
    return () => { document.body.style.overflow = 'hidden'; };
  }, [isOpen]);

  const selectedGradeInfo = GRADES.find(g => g.value === selectedGrade) || GRADES[5];

  const modalContent = (
    <div className="modal-overlay animate-fade-in" onClick={() => setIsOpen(false)}>
      <div className="grade-modal glass-panel animate-scale-in" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">
            <Award size={20} className="grade-icon" />
            <h2>Select Passing Threshold</h2>
          </div>
          <button className="close-modal-btn" onClick={() => setIsOpen(false)}>
            <X size={20} />
          </button>
        </div>
        
        <div className="modal-scroll-area">
          {GRADES.map((grade) => (
            <div 
              key={grade.value} 
              className={`grade-card-item ${selectedGrade === grade.value ? 'selected' : ''} ${getGradeColorClass(grade.value)}`}
              onClick={() => {
                onSelect(grade.value);
                setIsOpen(false);
              }}
            >
              <div className="card-letter-large">{grade.value}</div>
              <div className="card-info">
                <div className="card-desc-text">{grade.description}</div>
              </div>
              {selectedGrade === grade.value && <Check size={20} className="card-check-icon" />}
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  return (
    <div className="grade-selector-container">
      <div className="grade-selector-header">
        <Award size={14} className="grade-icon" />
        <span>Passing Threshold</span>
      </div>
      
      <button 
        className="grade-trigger-btn"
        onClick={() => setIsOpen(true)}
      >
        <span className={`grade-value-preview ${getGradeColorClass(selectedGradeInfo.value)}`}>{selectedGradeInfo.value}</span>
        <span className="grade-trigger-text">Set Minimum Grade</span>
        <ChevronDown size={16} className="chevron" />
      </button>

      <div className="grade-description-preview">
        "{selectedGradeInfo.description}"
      </div>

      {isOpen && createPortal(modalContent, document.body)}
    </div>
  );
};

export default GradeSelector;
