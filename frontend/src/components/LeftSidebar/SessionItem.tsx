import React from 'react';
import { ChatTeardropText } from "@phosphor-icons/react/dist/icons/ChatTeardropText";
import { CheckCircle } from "@phosphor-icons/react/dist/icons/CheckCircle";
import { WarningCircle } from "@phosphor-icons/react/dist/icons/WarningCircle";
import { Spinner } from "@phosphor-icons/react/dist/icons/Spinner";
import { CircleDashed } from "@phosphor-icons/react/dist/icons/CircleDashed";
import './SessionItem.css';
import type { Session } from '../../types'; 

interface SessionItemProps {
  session: Session; 
  isExpanded: boolean;
  isSelected: boolean;
  onClick: () => void;
}

const SessionItem: React.FC<SessionItemProps> = ({ session, isExpanded, isSelected, onClick }) => {
  const getStatusIcon = () => {
    const iconSize = isExpanded ? 18 : 20;
    switch (session.status) {
      case 'active':
        return <Spinner size={iconSize} className="session-status-icon status-active" />; 
      case 'completed':
        return <CheckCircle size={iconSize} weight="fill" className="session-status-icon status-completed" />;
      case 'error':
        return <WarningCircle size={iconSize} weight="fill" className="session-status-icon status-error" />;
      case 'pending':
        return <CircleDashed size={iconSize} className="session-status-icon status-pending" />;
      default:
        return <ChatTeardropText size={iconSize} className="session-icon" />;
    }
  };

  return (
    <button
      className={`session-item ${isSelected ? 'selected' : ''} ${!isExpanded ? 'collapsed' : ''}`}
      onClick={onClick}
      title={session.name}
    >
      <span className="session-icon-wrapper">
        {getStatusIcon()}
      </span>
      {isExpanded && <span className="session-name">{session.name}</span>}
      {!isExpanded && <span className="sr-only">{session.name}</span>}
    </button>
  );
};
export default SessionItem;