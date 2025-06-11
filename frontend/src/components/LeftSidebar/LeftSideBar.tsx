
import React from 'react';
import { Plus, ChevronLeft, ChevronRight, DiamondPlus } from 'lucide-react'; 
import './LeftSideBar.css';
import NewTaskButton from './NewTaskButton'; 
import SessionItem from './SessionItem';
import type { Session } from '../../types';

interface LeftSidebarProps {
    isExpanded: boolean;
    onToggle: () => void;
    sessions: Session[];
    currentSessionId: string | null;
    onNewTask: () => void;
    onSelectSession: (sessionId: string) => void;
}

const LeftSideBar: React.FC<LeftSidebarProps> = ({
                                                     isExpanded,
                                                     onToggle,
                                                     sessions,
                                                     currentSessionId,
                                                     onNewTask,
                                                     onSelectSession,
                                                 }) => {
    return (
        <aside className={`left-sidebar ${isExpanded ? 'expanded' : 'collapsed'}`}>
            {}
            <div className="sidebar-header">
                {}
                <button onClick={onToggle} className="toggle-button" aria-label={isExpanded ? "Collapse sidebar" : "Expand sidebar"}>
                    {isExpanded ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
                </button>
            </div>

            {isExpanded ? (
                
                <>
                    {}
                    <div className="sidebar-top-actions">
                        <span className="sidebar-app-title-standalone">Cerno</span>
                        {}
                        <div className="new-task-button-container-expanded">
                            {}
                            <NewTaskButton onClick={onNewTask} />
                            {}
                        </div>
                    </div>

                    <nav className="session-list">
                        {sessions.map((session) => (
                            <SessionItem
                                key={session.id}
                                session={session}
                                isExpanded={isExpanded}
                                isSelected={session.id === currentSessionId}
                                onClick={() => onSelectSession(session.id)}
                            />
                        ))}
                    </nav>
                </>
            ) : (
                
                <div className="collapsed-new-task-area">
                    <button
                        onClick={onNewTask}
                        className="collapsed-new-task-button"
                        title="New Task"
                        aria-label="Start a new task"
                    >
                        <DiamondPlus size={28} strokeWidth={1.25} />
                    </button>
                </div>
            )}
        </aside>
    );
};

export default LeftSideBar;
