import React, { useRef, useEffect, useState } from 'react';
import type { MessageData, GroupedModels } from '../../types';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import ModelSelector from './ModelSelector';
import EmptyState from './EmptyState';
import './MainChatWindow.css';
import { Files } from "@phosphor-icons/react/dist/icons/Files";
import { X } from "@phosphor-icons/react/dist/icons/X";

interface MainChatWindowProps {
    messages: MessageData[];
    onSendMessage: (messageText: string) => void;
    onStopRequest: () => void; // NEW
    isTaskRunning: boolean;
    currentTaskName?: string;
    onToggleRightPanel: () => void;
    isRightPanelVisible: boolean;
    effectiveRightPanelWidth: number;
    availableModels: GroupedModels;
    selectedModelId: string;
    onModelChange: (modelId: string) => void;
    isLoadingModels: boolean;
}

const MainChatWindow: React.FC<MainChatWindowProps> = ({
                                                           messages,
                                                           onSendMessage,
                                                           onStopRequest, // NEW
                                                           isTaskRunning,
                                                           currentTaskName,
                                                           onToggleRightPanel,
                                                           isRightPanelVisible,
                                                           effectiveRightPanelWidth,
                                                           availableModels,
                                                           selectedModelId,
                                                           onModelChange,
                                                           isLoadingModels,
                                                       }) => {
    const chatHistoryRef = useRef<HTMLDivElement>(null);
    const [inputText, setInputText] = useState('');

    useEffect(() => {
        if (chatHistoryRef.current) {
            chatHistoryRef.current.scrollTop = chatHistoryRef.current.scrollHeight;
        }
    }, [messages]);

    // Handler for EmptyState only
    const handleEmptySend = () => {
        if (inputText.trim() === '') return;
        onSendMessage(inputText);
        setInputText('');
    };

    const marginRight = isRightPanelVisible ? `${effectiveRightPanelWidth}px` : '0px';

    return (
        <div className="main-chat-window-container">
            <div
                className="main-chat-content-area"
                style={{ marginRight }}
            >
                {messages.length === 0 ? (
                    <EmptyState
                        availableModels={availableModels}
                        selectedModelId={selectedModelId}
                        onModelChange={onModelChange}
                        isLoadingModels={isLoadingModels}
                        onSendMessage={onSendMessage}
                        inputText={inputText}
                        setInputText={setInputText}
                        handleSendMessage={handleEmptySend}
                    />
                ) : (
                    <>
                        <header className="chat-header">
                            <ModelSelector
                                models={availableModels}
                                selectedModelId={selectedModelId}
                                onModelChange={onModelChange}
                                isLoading={isLoadingModels}
                            />
                            <div className="chat-header-actions">
                                {currentTaskName && (
                                    <h2 className="chat-task-title">{currentTaskName}</h2>
                                )}
                                <button
                                    onClick={onToggleRightPanel}
                                    className="toggle-right-panel-button"
                                    title={isRightPanelVisible ? "Hide File Workspace" : "Show File Workspace"}
                                >
                                    {isRightPanelVisible ? <X size={22} /> : <Files size={22} />}
                                </button>
                            </div>
                        </header>

                        <div className="chat-history-area" ref={chatHistoryRef}>
                            {messages.map(msg => (
                                <ChatMessage key={msg.id} message={msg} />
                            ))}
                        </div>

                        <div className="chat-bottom-container">
                            <ChatInput
                                onSendMessage={onSendMessage}
                                onStopRequest={onStopRequest}
                                isTaskRunning={isTaskRunning}
                            />
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

export default MainChatWindow;
