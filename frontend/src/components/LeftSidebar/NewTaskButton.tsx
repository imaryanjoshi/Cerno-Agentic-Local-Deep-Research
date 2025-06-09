
import React from 'react';
import { Plus } from 'lucide-react';

interface NewTaskButtonProps {
    onClick: () => void;
}

const NewTaskButton: React.FC<NewTaskButtonProps> = ({ onClick }) => {
    return (
        <button className="new-task-button-expanded-style" onClick={onClick}>
            {}
            <span className="new-task-btn-icon">
                <Plus size={16} strokeWidth={2.5} />
            </span>
            {}
            <span className="new-task-btn-text">New Task</span>
        </button>
    );
};

export default NewTaskButton;