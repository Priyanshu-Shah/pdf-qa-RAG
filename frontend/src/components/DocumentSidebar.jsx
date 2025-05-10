import { useRef } from 'react';
import { useFileContext } from '../context/FileContext';
import LoadingIndicator from './LoadingIndicator';
import ProcessingMethodSelector from './ProcessingMethodSelector';
import './DocumentSidebar.css';

function DocumentSidebar() {
  const fileInputRef = useRef(null);
  const { uploadedFiles, uploadFile, removeFile, isProcessing, processingMethod } = useFileContext();
  
  const handleFileChange = async (e) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      await processFiles(Array.from(files));
    }
    e.target.value = '';
  };
  
  const processFiles = async (files) => {
    // Log the currently selected processing method from context
    console.log('Current processing method from context:', processingMethod);
    
    for (const file of files) {
      if (file.type === 'application/pdf') {
        // Don't try to access file.method here as it doesn't exist yet
        await uploadFile(file);
      }
    }
  };
  
  const formatFileSize = (bytes) => {
    if (bytes < 1024) {
      return bytes + ' B';
    } else if (bytes < 1048576) {
      return (bytes / 1024).toFixed(1) + ' KB';
    } else {
      return (bytes / 1048576).toFixed(1) + ' MB';
    }
  };


  return (
    <div className="document-sidebar">
      <div className="sidebar-header">
        <h3>Your Documents</h3>
        <button 
          className="upload-button" 
          onClick={() => fileInputRef.current.click()}
          title="Upload PDF"
        >
          <svg width="20" height="20" viewBox="0 0 24 24">
            <path fill="currentColor" d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
          </svg>
        </button>
        <input
          ref={fileInputRef}
          type="file"
          className="hidden-file-input"
          accept=".pdf"
          multiple
          onChange={handleFileChange}
        />
      </div>
      
      <ProcessingMethodSelector />
      
      {isProcessing && (
        <div className="processing-indicator">
          <LoadingIndicator />
          <span>Processing...</span>
        </div>
      )}
      
      <div className="document-list">
        {uploadedFiles.length === 0 ? (
          <div className="empty-list">
            <p>No documents uploaded yet</p>
            <button 
              className="upload-first-document" 
              onClick={() => fileInputRef.current.click()}
            >
              Upload your first PDF
            </button>
          </div>
        ) : (
          uploadedFiles.map((file) => (
            <div 
              key={file.id} 
              className={`document-item ${file.status === 'uploading' ? 'uploading' : ''}`}
            >
              <div className="document-icon">
                {file.method === 'semantic' ? (
                  <svg viewBox="0 0 24 24" width="24" height="24">
                    <path fill="currentColor" d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 12H8v-2h8v2zm0-4H8V8h8v2zm-3-5V3.5L18.5 9H13z" />
                  </svg>
                ) : file.method === 'layout' ? (
                  <svg viewBox="0 0 24 24" width="24" height="24">
                    <path fill="currentColor" d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 7h5v5h-5v-5zM5 7h5v5H5V7zm0 10v-3h5v3H5zm12 0v-3h2v3h-2z" />
                  </svg>
                ) : (
                  <svg viewBox="0 0 24 24" width="24" height="24">
                    <path fill="currentColor" d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm0 16H6v-2h8v2zm0-4H6v-2h8v2zm-3-5V3.5L18.5 11H11z" />
                  </svg>
                )}
              </div>
              
              <div className="document-info">
                <div className="document-name-container">
                  <span className="document-name" title={file.name}>
                    {file.name.length > 25 ? file.name.substring(0, 25) + '...' : file.name}
                  </span>
                  <span className="document-size">{formatFileSize(file.size)}</span>
                </div>
                
                {file.status === 'uploading' && (
                  <div className="progress-bar">
                    <div className="progress" style={{width: `${file.progress}%`}}></div>
                  </div>
                )}
                {file.method && file.status === 'processed' && (
                  <div className="document-method">
                    {file.method === 'semantic' ? '📑 Semantic' : 
                     file.method === 'layout' ? '📊 Layout' : '📄 Standard'}
                  </div>
                )}
              </div>
              
              <button
                className="remove-document-btn"
                onClick={() => removeFile(file.id)}
                title="Remove document"
              >
                <svg viewBox="0 0 24 24" width="18" height="18">
                  <path fill="currentColor" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z" />
                </svg>
              </button>
            </div>
          ))
        )}
      </div>
      
      <div className="sidebar-footer">
        <div className="doc-count">
          {uploadedFiles.filter(f => f.status === 'processed').length} documents available
        </div>
      </div>
    </div>
  );
}

export default DocumentSidebar;