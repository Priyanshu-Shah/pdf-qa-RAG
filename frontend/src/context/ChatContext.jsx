/* eslint-disable react-hooks/exhaustive-deps */
/* eslint-disable react-refresh/only-export-components */
import { createContext, useState, useContext, useEffect } from 'react';
import { useFileContext } from './FileContext';
import { sendMessage } from '../services/api';

// Create context
const ChatContext = createContext();

export function ChatProvider({ children }) {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedDocuments, setSelectedDocuments] = useState([]);
  const { uploadedFiles } = useFileContext();
  const [chatHistory, setChatHistory] = useState([]);

  // When uploaded files change, update the selected documents if needed
  useEffect(() => {
    // Auto-select processed files that aren't already selected
    const processedFileIds = uploadedFiles
      .filter(file => file.status === 'processed')
      .map(file => file.id);
      
    // Check if we need to update selections based on processed files
    const needsUpdate = processedFileIds.some(id => !selectedDocuments.includes(id));
    
    if (needsUpdate) {
      setSelectedDocuments(processedFileIds);
    }
  }, [uploadedFiles]);

  /**
   * Send a user message and get AI response
   */
  const sendUserMessage = async (messageText) => {
    if (!messageText.trim()) return;
    
    // Add user message immediately
    const userMessage = {
      id: Date.now(),
      sender: 'user',
      text: messageText,
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);
    
    try {
      // Get active file IDs to query against
      const fileIds = selectedDocuments;
      
      if (fileIds.length === 0) {
        throw new Error('No documents selected. Please upload and select at least one document.');
      }
      
      // Add message to chat history
      const updatedHistory = [...chatHistory, {role: 'user', content: messageText}];
      setChatHistory(updatedHistory);
      
      // Send request to API
      const response = await sendMessage(messageText, fileIds);
      
      // Add AI response to messages
      const aiMessage = {
        id: Date.now() + 1,
        sender: 'ai',
        text: response.text || response.message || 'Sorry, I couldn\'t find an answer in your documents.',
        timestamp: new Date().toISOString(),
        sources: response.sources || [],
        metadata: response.metadata || {}
      };
      
      setMessages(prev => [...prev, aiMessage]);
      
      // Update chat history
      setChatHistory([...updatedHistory, {role: 'assistant', content: aiMessage.text}]);
      
    } catch (err) {
      console.error('Error sending message:', err);
      setError(err.message || 'Failed to get a response');
      
      // Add error message to chat
      const errorMessage = {
        id: Date.now() + 1,
        sender: 'system',
        text: `Error: ${err.message || 'Failed to get a response'}`,
        timestamp: new Date().toISOString(),
        isError: true
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };
  
  /**
   * Add a message directly to the chat (for system messages, etc.)
   */
  const addMessage = (message) => {
    const formattedMessage = {
      id: Date.now(),
      timestamp: new Date().toISOString(),
      ...message
    };
    
    setMessages(prev => [...prev, formattedMessage]);
  };
  
  /**
   * Clear all messages from the chat
   */
  const clearChat = () => {
    setMessages([]);
    setChatHistory([]);
  };
  
  /**
   * Toggle selection of a document for querying
   */
  const toggleDocumentSelection = (fileId) => {
    setSelectedDocuments(prev => 
      prev.includes(fileId)
        ? prev.filter(id => id !== fileId)
        : [...prev, fileId]
    );
  };

  // Create context value object
  const contextValue = {
    messages,
    isLoading,
    error,
    selectedDocuments,
    chatHistory,
    setMessages,
    setIsLoading,
    sendUserMessage,
    addMessage,
    clearChat,
    setSelectedDocuments,
    toggleDocumentSelection
  };

  return (
    <ChatContext.Provider value={contextValue}>
      {children}
    </ChatContext.Provider>
  );
}

// Custom hook for easier context consumption
export function useChatContext() {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChatContext must be used within a ChatProvider');
  }
  return context;
}

export default ChatContext;