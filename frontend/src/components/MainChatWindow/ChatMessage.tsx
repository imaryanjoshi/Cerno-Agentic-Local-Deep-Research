import React from 'react'; 
import type { MessageData, AgentMessageData, TaskStepData, AgentAction } from '../../types';
import { CheckCircle } from "@phosphor-icons/react/dist/icons/CheckCircle";
import { WarningCircle } from "@phosphor-icons/react/dist/icons/WarningCircle";
import { Spinner } from "@phosphor-icons/react/dist/icons/Spinner";
import { CircleDashed } from "@phosphor-icons/react/dist/icons/CircleDashed";
import { CaretUp } from "@phosphor-icons/react/dist/icons/CaretUp";
import { TerminalWindow } from "@phosphor-icons/react/dist/icons/TerminalWindow";
import { FileText as PhosphorFileText } from "@phosphor-icons/react/dist/icons/FileText"; 
import { MagnifyingGlass } from "@phosphor-icons/react/dist/icons/MagnifyingGlass";
import { HandPalm  } from "@phosphor-icons/react/dist/icons/HandPalm";
import { Copy as PhosphorCopy } from "@phosphor-icons/react/dist/icons/Copy";

import './ChatMessage.css';
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
const getAgentActionIcon = (action: AgentAction) => {
    const iconSize = 16;

    // For delegated tasks, check the agent ID
    if (action.type === 'delegated_task' && action.memberAgentId) {
        if (action.memberAgentId.includes('research')) {
            return <MagnifyingGlass size={iconSize} className="action-icon-research" />;
        }
        if (action.memberAgentId.includes('composer')) {
            return <PhosphorFileText size={iconSize} className="action-icon-composer" />;
        }
    }

    // Fallback for generic tool calls or unknown delegated agents
    return <TerminalWindow size={iconSize} className="action-icon-generic-tool" />;
};
const SimpleCodeBlock: React.FC<{ language: string; content: string }> = ({ language, content }) => {
  const handleCopy = () => {
    navigator.clipboard.writeText(content).catch(err => console.error("Failed to copy code:", err));
    
  };
  return (
    <div className="code-block-container">
      <div className="code-block-header">
        {}
        <button onClick={handleCopy} className="code-block-copy-button" title="Copy code">
          <PhosphorCopy size={16} />
        </button>
      </div>
      <pre className={`language-${language}`}>
        <code>{content}</code>
      </pre>
    </div>
  );
};

const AgentActionChip: React.FC<{ action: AgentAction }> = ({ action }) => {
    const getStatusIndicator = () => {
        switch (action.status) {
            case 'running': return <Spinner size={14} className="action-status-icon spinning" />;
            case 'success': return <CheckCircle size={14} weight="fill" className="action-status-success" />;
            case 'error': return <WarningCircle size={14} weight="fill" className="action-status-error" />;
            default: return null;
        }
    };

    return (
        <div className={`agent-action-chip status-${action.status || 'pending'}`}>
            <div className="action-icon-wrapper">
                {getAgentActionIcon(action)}
            </div>
            <div className="action-text-wrapper">
                {/* CHANGE IS HERE: The colon is removed from the JSX */}
                <span className="action-prefix">{action.prefix}</span>
                <span className="action-detail">{action.detail}</span>
            </div>
            <div className="action-status-indicator">
                {getStatusIndicator()}
            </div>
        </div>
    );
};

const TaskStepDisplay: React.FC<{ step: TaskStepData, isLastStep: boolean }> = ({ step, isLastStep }) => {
  const getStatusIcon = () => {
    const iconSize = 18;
    switch (step.status) {
      case 'success': return <CheckCircle size={iconSize} weight="fill" className="status-icon success" />;
      case 'error': return <WarningCircle size={iconSize} weight="fill" className="status-icon error" />;
      case 'running': return <Spinner size={iconSize} className="status-icon running" />; 
      case 'pending': return <CircleDashed size={iconSize} className="status-icon pending" />;
        case 'stopped':
            return <HandPalm size={iconSize} weight="fill" className="status-icon stopped" />;
      default: return <CircleDashed size={iconSize} className="status-icon default" />;
    }
  };

    return (
        <li className={`task-step ${step.status} ${step.isActive ? 'active' : ''}`}>
            <div className="step-timeline">
                <div className="step-status-icon-wrapper">{getStatusIcon()}</div>
                {!isLastStep && <div className="step-connector-line"></div>}
            </div>
            <div className="step-content">
                {}
                {step.description && <p className="step-description">{step.description}</p>}

                {}
                {}

                {}
                {step.agentActions && step.agentActions.length > 0 && (
                    <div className="agent-actions-container">
                        {step.agentActions.map(action => <AgentActionChip key={action.id} action={action} />)}
                    </div>
                )}
            </div>
        </li>
    );
};

const ChatMessage: React.FC<{ message: MessageData }> = ({ message }) => {
  const isAgent = message.sender === 'agent';
  const agentMessage = isAgent ? (message as AgentMessageData) : null;

  const getTaskOverallStatusIcon = (iconType?: 'check' | 'loader' | 'error') => {
    if (!iconType) return null;
    const iconSize = 20;
    if (iconType === 'check') return <CheckCircle size={iconSize} weight="fill" className="task-title-status-icon success" />;
    if (iconType === 'loader') return <Spinner size={iconSize} className="task-title-status-icon running" />; 
    if (iconType === 'error') return <WarningCircle size={iconSize} weight="fill" className="task-title-status-icon error" />;
    return null;
  };

  return (
    <div className={`chat-message-wrapper ${isAgent ? 'agent' : 'user'}`}>
      <div className={`chat-message-bubble ${agentMessage?.task ? 'has-task' : ''} ${!isAgent ? 'user-bubble' : ''}`}>
        {}
        {message.sender === 'user' && <p className="message-text">{message.text}</p>}
        {agentMessage && !agentMessage.task && !agentMessage.codeBlock && agentMessage.text && (
          <p className="message-text">{agentMessage.text}</p>
        )}

        {}
        {agentMessage?.task && (
            <div className="task-progress-container">
                <div className="task-main-header">
                    {getTaskOverallStatusIcon(agentMessage.task.statusIcon)}
                    <h3 className="task-overall-title">{agentMessage.task.title}</h3>
                    {agentMessage.task.isCollapsible && (
                        <button className="task-collapse-toggle" aria-label="Toggle task details">
                            <CaretUp size={18} />
                        </button>
                    )}
                </div>
                {agentMessage.task.steps && agentMessage.task.steps.length > 0 && (
                    <ul className="task-steps-list">
                        {agentMessage.task.steps.map((step, index, arr) => (
                            
                            step ? <TaskStepDisplay key={step.id || `step-${index}`} step={step} isLastStep={index === arr.length - 1} /> : null
                        ))}
                    </ul>
                )}
                {agentMessage.task.summary && (
                    <p className="task-summary">{agentMessage.task.summary}</p>
                )}
            </div>
        )}

        {}
        {agentMessage?.codeBlock && (
          <SimpleCodeBlock language={agentMessage.codeBlock.language} content={agentMessage.codeBlock.content} />
        )}

        {}
        {(message.sender === 'user' || (agentMessage && !agentMessage.task && !agentMessage.codeBlock)) && (
             <span className="message-timestamp">
                {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
             </span>
        )}
      </div>
    </div>
  );
};

export default ChatMessage;