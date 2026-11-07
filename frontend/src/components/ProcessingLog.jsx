import React, { useEffect, useRef } from 'react';
import { 
  Users, UserCheck, GraduationCap, Map, Brain, 
  ShieldCheck, GitMerge, LayoutDashboard, Loader2,
  CheckCircle2, MessageSquare, AlertCircle
} from 'lucide-react';
import './ProcessingLog.css';

const agentIcons = {
  'recruiter': Users,
  'council_member': UserCheck,
  'pedagogical_expert': GraduationCap,
  'cartographer': Map,
  'expert': Brain,
  'validator': ShieldCheck,
  'synthesizer': GitMerge,
  'structural_auditor': LayoutDashboard,
  'branch_worker': Brain,
  'resolution': AlertCircle
};

const agentColors = {
  'recruiter': '#818cf8',
  'council_member': '#60a5fa',
  'pedagogical_expert': '#34d399',
  'cartographer': '#fbbf24',
  'expert': '#a78bfa',
  'validator': '#f87171',
  'synthesizer': '#2dd4bf',
  'structural_auditor': '#fb7185',
  'branch_worker': '#a78bfa',
  'resolution': '#f472b6'
};

const ProcessingLog = ({ events, isProcessing }) => {
  const logEndRef = useRef(null);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  const activeAgent = events.length > 0 && events[events.length - 1].type === 'start' 
    ? events[events.length - 1].agent 
    : null;

  return (
    <div className="processing-log-container glass-panel">
      <div className="processing-log-header">
        <h3>Pipeline Activity</h3>
        {isProcessing && (
          <div className="active-agent-badge">
            <Loader2 className="spin" size={14} />
            <span>{activeAgent ? `Agent ${activeAgent} active` : 'Processing...'}</span>
          </div>
        )}
      </div>
      
      <div className="processing-log-events">
        {events.length === 0 && (
          <div className="empty-log">
            <p>Waiting for pipeline events...</p>
          </div>
        )}
        
        {events.map((event, index) => {
          const agentName = event.agent || 'Unknown Agent';
          let agentKey = agentName.toLowerCase();
          
          // Map specialized names to base agent types for icons/colors
          if (agentKey.includes('expert (')) agentKey = 'expert';
          
          // If it's a council role (not in our base map), use council_member as fallback
          const isKnownBaseAgent = !!agentIcons[agentKey];
          if (!isKnownBaseAgent && agentName !== 'LangGraph') {
            agentKey = 'council_member';
          }

          const Icon = agentIcons[agentKey] || MessageSquare;
          const color = agentColors[agentKey] || 'var(--text-secondary)';
          
          return (
            <div key={index} className={`log-event ${event.type} animate-fade-in`}>
              <div className="event-icon" style={{ backgroundColor: `${color}22`, color: color }}>
                {event.type === 'start' ? <Loader2 className="spin" size={16} /> : <Icon size={16} />}
              </div>
              
              <div className="event-content">
                <div className="event-meta">
                  <span className="agent-name" style={{ color: color }}>{agentName}</span>
                  <span className="timestamp">{new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
                </div>
                
                {event.type === 'message' && (
                  <p className="event-text">{event.content}</p>
                )}
                
                {event.type === 'start' && (
                  <p className="event-status">Started working...</p>
                )}
              </div>
            </div>
          );
        })}
        <div ref={logEndRef} />
      </div>
    </div>
  );
};

export default ProcessingLog;
