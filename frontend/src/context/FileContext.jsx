/* eslint-disable react-refresh/only-export-components */
import { createContext, useState, useContext } from 'react';
import { uploadPDF, deleteFile, getUploadedFiles } from '../services/api';

// Create context
const FileContext = createContext();

export function FileProvider({ children }) {
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const [error, setError] = useState(null);

  /**
   * Upload and process a new PDF file
   */
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
      thumbnail: null,
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

      // Send to server
      const response = await uploadPDF(file, onProgress);
      
      // Update file with server response
      setUploadedFiles(prev => 
        prev.map(f => 
          f.id === tempFileId 
            ? { 
                ...f, 
                id: response.fileId || f.id, 
                status: 'processed',
                progress: 100,
                serverData: response.data || {} 
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

  /**
   * Remove a file from the list and optionally from the server
   */
  const removeFile = async (fileId, removeFromServer = true) => {
    try {
      if (removeFromServer) {
        await deleteFile(fileId);
      }
    } catch (err) {
      console.error('Error removing file from server:', err);
      setError(err.message || 'Failed to remove file from server');
    }

    // Remove from state regardless of server response
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
    
    // Also clean up progress data
    setUploadProgress(prev => {
      const newProgress = { ...prev };
      delete newProgress[fileId];
      return newProgress;
    });
  };

  /**
   * Fetch all uploaded files from server
   */
  const fetchFiles = async () => {
    setIsProcessing(true);
    setError(null);
    
    try {
      const files = await getUploadedFiles();
      setUploadedFiles(files.map(file => ({
        ...file,
        status: 'processed',
        progress: 100
      })));
    } catch (err) {
      console.error('Error fetching files:', err);
      setError(err.message || 'Failed to fetch uploaded files');
    } finally {
      setIsProcessing(false);
    }
  };

  /**
   * Update status of a single file
   */
  const updateFileStatus = (fileId, status) => {
    setUploadedFiles(prev => 
      prev.map(file => 
        file.id === fileId ? { ...file, status } : file
      )
    );
  };
  
  /**
   * Check if we have any files that are ready to be used in chat
   */
  const hasProcessedFiles = () => {
    return uploadedFiles.some(file => file.status === 'processed');
  };

  // Create context value object
  const contextValue = {
    uploadedFiles,
    isProcessing,
    uploadProgress,
    error,
    setUploadedFiles,
    setIsProcessing,
    uploadFile,
    removeFile,
    fetchFiles,
    updateFileStatus,
    hasProcessedFiles
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
  if (context === undefined) {
    throw new Error('useFileContext must be used within a FileProvider');
  }
  return context;
}

export default FileContext;