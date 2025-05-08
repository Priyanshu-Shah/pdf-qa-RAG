import { useFileContext } from '../context/FileContext';
import PDFThumbnail from './PDFThumbnail';
import './UploadedFilesList.css';

function UploadedFilesList({ onChatStart }) {
  const { uploadedFiles, removeFile } = useFileContext();
  
  if (uploadedFiles.length === 0) {
    return null;
  }
  
  return (
    <div className="uploaded-files-container">
      <h2 className="section-title">Uploaded Files</h2>
      
      <div className="files-grid">
        {uploadedFiles.map((file) => (
          <div className="file-card" key={file.id}>
            <PDFThumbnail file={file} />
            
            <div className="file-info">
              <div className="file-name-container">
                <span className="file-name" title={file.name}>
                  {file.name.length > 20 ? file.name.substring(0, 20) + '...' : file.name}
                </span>
                <span className="file-size">{formatFileSize(file.size)}</span>
              </div>
              
              <div className="file-status">
                {file.status === 'uploading' && (
                  <span className="status uploading">
                    <div className="spinner"></div> Processing...
                  </span>
                )}
                
                {file.status === 'processed' && (
                  <span className="status processed">
                    <svg viewBox="0 0 24 24" width="16" height="16">
                      <path fill="currentColor" d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" />
                    </svg> 
                    Ready
                  </span>
                )}
                
                {file.status === 'error' && (
                  <span className="status error">
                    <svg viewBox="0 0 24 24" width="16" height="16">
                      <path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
                    </svg>
                    Error
                  </span>
                )}
              </div>
            </div>
            
            <button 
              className="remove-file-btn" 
              onClick={(e) => {
                e.stopPropagation();
                removeFile(file.id);
              }}
            >
              <svg viewBox="0 0 24 24" width="16" height="16">
                <path fill="currentColor" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z" />
              </svg>
            </button>
          </div>
        ))}
      </div>
      
      {uploadedFiles.length > 0 && uploadedFiles.some(file => file.status === 'processed') && (
        <div className="actions-container">
          <button className="start-chat-btn" onClick={onChatStart}>
            Start Chatting With Your Documents
          </button>
        </div>
      )}
    </div>
  );
}

function formatFileSize(bytes) {
  if (bytes < 1024) {
    return bytes + ' B';
  } else if (bytes < 1048576) {
    return (bytes / 1024).toFixed(1) + ' KB';
  } else {
    return (bytes / 1048576).toFixed(1) + ' MB';
  }
}

export default UploadedFilesList;