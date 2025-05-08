import { createContext, useState, useContext } from 'react';

const ChatContext = createContext();

export function ChatProvider({ children }) {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedDocuments, setSelectedDocuments] = useState([]);
  
  const addMessage = (message) => {
    setMessages(prev => [...prev, message]);
  };
  
  const clearChat = () => {
    setMessages([]);
  };

  return (
    <ChatContext.Provider value={{
      messages,
      setMessages,
      isLoading,
      setIsLoading,
      addMessage,
      clearChat,
      selectedDocuments,
      setSelectedDocuments
    }}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChatContext() {
  return useContext(ChatContext);
}