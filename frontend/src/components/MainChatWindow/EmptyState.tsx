import React from 'react';
import {motion} from 'framer-motion';
import {PaperPlaneTilt} from '@phosphor-icons/react';
import ModelSelector, {type GroupedModels} from './ModelSelector'; // Assuming ModelSelector exists
import './EmptyState.css';
import ChatInput from "./ChatInput.tsx";

interface EmptyStateProps {
    availableModels: GroupedModels,
    selectedModelId: string,
    onModelChange: (modelId: string) => void,
    isLoadingModels: boolean,
    inputText: string,
    setInputText: (text: string) => void,
    handleSendMessage: () => void,
    onSendMessage?: (messageText: string) => void
}

const EmptyState: React.FC<EmptyStateProps> = ({
                                                   availableModels,
                                                   selectedModelId,
                                                   onModelChange,
                                                   isLoadingModels,
                                                   inputText,
                                                   setInputText,
                                                   handleSendMessage,
                                                   onSendMessage
                                               }) => {

    const handleKeyPress = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            if (inputText.trim()) {
                handleSendMessage();
            }
        }
    };
    const handleSend = () => {
        if (inputText.trim() === '') return;
        // Call the handler passed down from App.tsx
        onSendMessage(inputText);
        setInputText(''); // Clear the local input
    };
    return (
        <div className="empty-state-container">
            <div style={{flexGrow: 1}}></div>
            <motion.div
                className="empty-state-content"
                initial={{opacity: 0, y: 20}}
                animate={{opacity: 1, y: 0}}
                transition={{duration: 0.5, ease: 'easeOut'}}
            >
                <h1 className="empty-state-title">What would you like to research today?</h1>

                <div className="empty-state-input-wrapper">
          <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Ask a question..."
              className="empty-state-textarea"
              rows={1}
              autoFocus
          />
                    <button
                        onClick={handleSendMessage}
                        className="empty-state-send-button"
                        title="Send message"
                        disabled={!inputText.trim()}
                    >
                        <PaperPlaneTilt size={22} weight="fill"/>
                    </button>
                </div>

                <div className="empty-state-model-selector-wrapper">
                    <ModelSelector
                        models={availableModels}
                        selectedModelId={selectedModelId}
                        onModelChange={onModelChange}
                        isLoading={isLoadingModels}
                    />

                </div>
            </motion.div>
            <div className="empty-state-spacer"></div>
        </div>
    );
};

export default EmptyState;