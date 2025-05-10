/* eslint-disable react-refresh/only-export-components */
import React, { createContext, useState, useContext, useEffect } from 'react';
import { uploadPDF, getUploadedFiles, deleteFile } from '../services/api';

// Create context
const FileContext = createContext();

export function FileProvider({ children }) {
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [selectedFileIds, setSelectedFileIds] = useState([]); // Add this line
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const [error, setError] = useState(null);
  const [processingMethod, setProcessingMethod] = useState('standard'); // Default method

  // Update the uploadFile function to correctly handle the method from server response:
  const uploadFile = async (file) => {
    // Create a temporary file object with pending status
    const tempFileId = Date.now() + Math.random().toString(36).substring(2, 10);
    const newFile = {
      id: tempFileId,
      file: file,
      name: file.name,
      size: file.size,
      status: 'uploading',
      progress: 0,
      method: processingMethod, // Initially set to selected method
      dateUploaded: new Date().toISOString()
    };

    // Add to state immediately to show in UI
    setUploadedFiles(prev => [...prev, newFile]);
    setIsProcessing(true);
    setError(null);

    try {
      // Track upload progress
      const onProgress = (progress) => {
        setUploadProgress(prev => ({
          ...prev,
          [tempFileId]: progress
        }));
        
        setUploadedFiles(prev => 
          prev.map(f => 
            f.id === tempFileId 
              ? { ...f, progress: progress } 
              : f
          )
        );
      };

      // Send to server with processing method
      const response = await uploadPDF(file, onProgress, processingMethod);
      console.log("File upload response:", response);
      
      // Get the actual method used from the server response
      const actualMethod = response.data?.method || processingMethod;
      
      console.log("File uploaded with method:", actualMethod);

      if(actualMethod != processingMethod) {
        console.log("Processing method fallen-back from", processingMethod, "to", actualMethod, "likely due to library inconsistency at backend");
        setProcessingMethod(actualMethod);
      }

      // Update file with server response
      setUploadedFiles(prev => 
        prev.map(f => 
          f.id === tempFileId 
            ? { 
                ...f, 
                id: response.fileId || f.id, 
                status: 'processed',
                progress: 100,
                serverData: response.data || {},
                method: actualMethod // Set the method returned from server
              } 
            : f
        )
      );

    } catch (err) {
      console.error('File upload error:', err);
      setError(err.message || 'Failed to upload file');
      
      // Update file status to error
      setUploadedFiles(prev => 
        prev.map(f => 
          f.id === tempFileId 
            ? { ...f, status: 'error', error: err.message } 
            : f
        )
      );
    } finally {
      setIsProcessing(false);
    }
  };

  const toggleFileSelection = (fileId) => {
    setSelectedFileIds(prev => {
      if (prev.includes(fileId)) {
        return prev.filter(id => id !== fileId);
      } else {
        return [...prev, fileId];
      }
    });
  };

  const selectAllFiles = () => {
    const processedFileIds = uploadedFiles
      .filter(file => file.status === 'processed')
      .map(file => file.id);
    setSelectedFileIds(processedFileIds);
  };

  const clearFileSelection = () => {
    setSelectedFileIds([]);
  };

  useEffect(() => {
    // Remove any selected IDs for files that no longer exist
    setSelectedFileIds(prev => 
      prev.filter(id => uploadedFiles.some(file => file.id === id))
    );
  }, [uploadedFiles]);
  

  const removeFile = async (fileId, removeFromServer = true) => {
    try {
      if (removeFromServer) {
        try {
          await deleteFile(fileId);
        } catch (err) {
          console.error('Error removing file from server:', err);
          setError(err.message || 'Failed to remove file from server');
        }
      }

      setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
      setUploadProgress(prev => {
        const newProgress = { ...prev };
        delete newProgress[fileId];
        return newProgress;
      });
    } catch (err) {
      console.error('Error in removeFile:', err);
    }
  };

  // Fetch all uploaded files from server
  const fetchFiles = async () => {
    try {
      setError(null);
      const files = await getUploadedFiles();
      
      if (files && Array.isArray(files)) {
        setUploadedFiles(files.map(file => ({
          id: file.id,
          name: file.name,
          size: file.size,
          status: 'processed',
          progress: 100,
          dateUploaded: file.dateUploaded,
          method: file.method || 'standard'
        })));
      }
    } catch (err) {
      console.error('Error fetching files:', err);
      setError('Failed to load files');
    }
  };

  // Update status of a single file
  const updateFileStatus = (fileId, status) => {
    setUploadedFiles(prev => 
      prev.map(f => 
        f.id === fileId 
          ? { ...f, status: status } 
          : f
      )
    );
  };
  
  // Check if we have any files that are ready to be used in chat
  const hasProcessedFiles = () => {
    return uploadedFiles.some(file => file.status === 'processed');
  };

  // Load files on initial render
  useEffect(() => {
    fetchFiles();
    console.log("filecontext - current processing method:", processingMethod);
  }, [processingMethod]);

  // Create context value object
  const contextValue = {
    uploadedFiles,
    isProcessing,
    uploadProgress,
    error,
    uploadFile,
    removeFile,
    fetchFiles,
    updateFileStatus,
    hasProcessedFiles,
    processingMethod,
    setProcessingMethod,
    selectedFileIds,
    toggleFileSelection,
    selectAllFiles,
    clearFileSelection
  };

  return (
    <FileContext.Provider value={contextValue}>
      {children}
    </FileContext.Provider>
  );
}

// Custom hook for easier context consumption
export function useFileContext() {
  const context = useContext(FileContext);
  if (!context) {
    throw new Error('useFileContext must be used within a FileProvider');
  }
  return context;
}

export default FileContext;