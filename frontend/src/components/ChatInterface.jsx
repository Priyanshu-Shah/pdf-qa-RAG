import { useState, useRef, useEffect } from 'react';
import { useChatContext } from '../context/ChatContext';
import { useFileContext } from '../context/FileContext';
import MessageBubble from './MessageBubble';
import LoadingIndicator from './LoadingIndicator';
import './ChatInterface.css';

function ChatInterface() {
  const [message, setMessage] = useState('');
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const chatContainerRef = useRef(null);
  
  const { messages, sendUserMessage, isLoading } = useChatContext();
  const { uploadedFiles, hasProcessedFiles } = useFileContext();
  
  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = '44px';
      const scrollHeight = textareaRef.current.scrollHeight;
      textareaRef.current.style.height = `${Math.min(scrollHeight, 120)}px`;
    }
  }, [message]);

  // Add this near the top of your component
  useEffect(() => {
    // Log whenever uploaded files change
    console.log("Uploaded files updated:", uploadedFiles);
    
    // Automatically select all processed files if needed
    const processedFiles = uploadedFiles.filter(file => file.status === 'processed');
    console.log("Processed files:", processedFiles);

  }, [uploadedFiles]);
  
  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!message.trim() || isLoading || !hasProcessedFiles()) return;
    
    await sendUserMessage(message);
    setMessage('');
  };
  
  // Handle Ctrl+Enter or Cmd+Enter to submit
  const handleKeyDown = (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      handleSubmit(e);
    }
  };

  return (
    <div className="chat-interface">
      <div className="chat-container" ref={chatContainerRef}>
        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="empty-chat">
              <div className="empty-chat-icon">💬</div>
              <h2>Ask questions about your documents</h2>
              <p>Upload PDFs using the sidebar and ask questions to get insights from your documents</p>
            </div>
          ) : (
            <>
              {messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
              ))}
            </>
          )}
          
          {isLoading && (
            <div className="ai-thinking">
              <LoadingIndicator />
              <span>Analyzing documents...</span>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
        
        <form onSubmit={handleSubmit} className="message-form">
          <div className="textarea-container">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={hasProcessedFiles() ? 
                "Ask a question about your documents..." : 
                "Upload PDF documents first to ask questions"}
              rows="1"
              disabled={!hasProcessedFiles()}
            />
          </div>
          
          <button 
            type="submit" 
            className="send-button"
            disabled={!message.trim() || isLoading || !hasProcessedFiles()}
            title={hasProcessedFiles() ? "Send message" : "Upload documents first"}
          >
            <svg viewBox="0 0 24 24" width="24" height="24">
              <path fill="currentColor" d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
}

export default ChatInterface;