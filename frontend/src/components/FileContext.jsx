import { createContext, useState, useContext } from 'react';

const FileContext = createContext();

export function FileProvider({ children }) {
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});

  const addFile = (file) => {
    setUploadedFiles(prev => [...prev, file]);
  };

  const removeFile = (fileId) => {
    setUploadedFiles(prev => prev.filter(file => file.id !== fileId));
  };
  
  const updateFileStatus = (fileId, status) => {
    setUploadedFiles(prev => 
      prev.map(file => 
        file.id === fileId ? { ...file, status } : file
      )
    );
  };

  return (
    <FileContext.Provider value={{
      uploadedFiles,
      isProcessing,
      uploadProgress,
      setUploadedFiles,
      setIsProcessing,
      setUploadProgress,
      addFile,
      removeFile,
      updateFileStatus
    }}>
      {children}
    </FileContext.Provider>
  );
}

export function useFileContext() {
  return useContext(FileContext);
}