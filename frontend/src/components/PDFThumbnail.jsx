import { useState, useEffect } from 'react';
import './PDFThumbnail.css';
import * as pdfjs from 'pdfjs-dist';

// Set worker source path
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

function PDFThumbnail({ file }) {
  const [thumbnail, setThumbnail] = useState(null);
  
  useEffect(() => {
    if (file && file.file) {
      generateThumbnail(file.file);
    }
  }, [file]);
  
  const generateThumbnail = async (pdfFile) => {
    try {
      // Read the file as ArrayBuffer using FileReader instead of arrayBuffer()
      const reader = new FileReader();
      
      // Create promise to handle FileReader async operation
      const arrayBufferPromise = new Promise((resolve, reject) => {
        reader.onload = () => resolve(reader.result);
        reader.onerror = () => reject(new Error('Failed to read file'));
        reader.readAsArrayBuffer(pdfFile);
      });
      
      // Get ArrayBuffer from FileReader
      const arrayBuffer = await arrayBufferPromise;
      
      // Load the PDF document
      const loadingTask = pdfjs.getDocument({ data: arrayBuffer });
      const pdf = await loadingTask.promise;
      
      // Get the first page
      const page = await pdf.getPage(1);
      
      // Calculate viewport with a reasonable scale for thumbnail
      const viewport = page.getViewport({ scale: 0.5 });
      
      // Create canvas
      const canvas = document.createElement('canvas');
      const context = canvas.getContext('2d');
      canvas.height = viewport.height;
      canvas.width = viewport.width;
      
      // Render to canvas
      await page.render({
        canvasContext: context,
        viewport: viewport
      }).promise;
      
      // Convert canvas to data URL
      const dataUrl = canvas.toDataURL();
      setThumbnail(dataUrl);
      
    } catch (error) {
      console.error('Error generating thumbnail:', error);
      // Set default thumbnail on error
      setThumbnail(null);
    }
  };
  
  return (
    <div className="pdf-thumbnail">
      {thumbnail ? (
        <img src={thumbnail} alt={`Thumbnail for ${file.name}`} className="thumbnail-img" />
      ) : (
        <div className="thumbnail-placeholder">
          <svg viewBox="0 0 24 24" width="40" height="40">
            <path fill="currentColor" d="M8 16h8v2H8zm0-4h8v2H8zm6-10H6c-1.1 0-2 .9-2 2v16c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm4 18H6V4h7v5h5v11z" />
          </svg>
        </div>
      )}
    </div>
  );
}

export default PDFThumbnail;