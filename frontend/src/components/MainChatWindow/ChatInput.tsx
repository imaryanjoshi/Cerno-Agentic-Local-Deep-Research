import React, { useState, useRef, useEffect } from 'react';
import { PaperPlaneTilt, Stop } from "@phosphor-icons/react"; // Import Stop icon
import { Paperclip as PhosphorPaperclip } from "@phosphor-icons/react/dist/icons/Paperclip"; 
import './ChatInput.css';

interface ChatInputProps {
  onSendMessage: (messageText: string) => void;
  isTaskRunning: boolean; // NEW PROP
  onStopRequest: () => void; // NEW: Dedicated prop for stopping

}

const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage, isTaskRunning,onStopRequest
}) => {
  const [inputText, setInputText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleInputChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputText(event.target.value);
    adjustTextareaHeight();
  };

  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'; 
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  };

  const handleSend = () => {
    if (inputText.trim() === '') return;
    onSendMessage(inputText.trim());
    setInputText('');
  };

  const handleKeyPress = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (isTaskRunning) return; // Don't send on Enter while running
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };
  useEffect(() => {
    adjustTextareaHeight(); 
  }, [inputText]);

  return (
    <div className="chat-input-container">
      <div className="chat-input-bar">
        <button className="chat-action-button file-button" title="Attach file">
          <PhosphorPaperclip size={22} /> {}
          <span className="sr-only">Attach file</span>
        </button>

        <textarea
            ref={textareaRef}
            value={inputText}
            onChange={handleInputChange}
            onKeyDown={handleKeyPress} // Changed to onKeyDown for better Enter handling
            placeholder={isTaskRunning ? "Task in progress..." : "Send a message..."}
            disabled={isTaskRunning}
            className="chat-textarea"
            rows={1}
        />

        {isTaskRunning ? (
            // --- RENDER STOP BUTTON ---
            <button
                onClick={onStopRequest} // Use the dedicated stop handler
                className="send-button stop-button"
                title="Stop Task"
            >
              <Stop size={22} weight="fill" />
            </button>
        ) : (
            // --- RENDER SEND BUTTON ---
            <button
                onClick={handleSend} // Use the dedicated send handler
                className="send-button"
                title="Send message"
                disabled={inputText.trim() === ''} // Disable if textarea is empty
            >
              <PaperPlaneTilt size={22} weight="fill" />
            </button>
        )}
      </div>
    </div>
  );
};

export default ChatInput;