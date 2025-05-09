// Base URL for your API
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';


// export const uploadPDF = async (file, onProgress) => {
//   const formData = new FormData();
//   formData.append('pdf', file);

//   try {
//     if (!API_BASE_URL.startsWith('http://localhost')) {
//       return simulateUpload(file, onProgress);
//     }
    
//     // XMLHttpRequest for upload progress tracking
//     return new Promise((resolve, reject) => {
//       const xhr = new XMLHttpRequest();
      
//       // Track progress if callback provided
//       if (onProgress && typeof onProgress === 'function') {
//         xhr.upload.onprogress = (event) => {
//           if (event.lengthComputable) {
//             const percentComplete = Math.round((event.loaded / event.total) * 100);
//             onProgress(percentComplete);
//           }
//         };
//       }
      
//       xhr.open('POST', `${API_BASE_URL}/upload`);
      
//       xhr.onload = () => {
//         if (xhr.status >= 200 && xhr.status < 300) {
//           try {
//             const response = JSON.parse(xhr.responseText);
//             resolve(response);
//           } catch (e) {
//             reject(new Error('Invalid response format'));
//             console.log(e);
//           }
//         } else {
//           reject(new Error(`Upload failed with status: ${xhr.status}`));
//         }
//       };
      
//       xhr.onerror = () => reject(new Error('Network error during upload'));
//       xhr.ontimeout = () => reject(new Error('Upload timed out'));
      
//       xhr.send(formData);
//     });
//   } catch (error) {
//     console.error('Error uploading PDF:', error);
//     throw error;
//   }
// };

// function simulateUpload(file, onProgress) {
//   return new Promise((resolve) => {
//     let progress = 0;
//     const interval = setInterval(() => {
//       progress += 10;
      
//       if (onProgress) {
//         onProgress(progress);
//       }
      
//       if (progress >= 100) {
//         clearInterval(interval);
        
//         setTimeout(() => {
//           resolve({
//             fileId: Date.now() + Math.random().toString(36).substring(2, 10),
//             filename: file.name,
//             size: file.size,
//             data: {
//               pages: Math.floor(Math.random() * 20) + 1,
//               processed: true
//             }
//           });
//         }, 500);
//       }
//     }, 300);
//   });
// }

export const uploadPDF = async (file, onProgress, processingMethod = 'standard') => {
  const formData = new FormData();
  formData.append('pdf', file);
  // Add the processing method to the form data
  formData.append('method', processingMethod);
  console.log(`api: Processing method for upload: ${processingMethod}`);
  try {
    if (!API_BASE_URL.startsWith('http://localhost')) {
      return simulateUpload(file, onProgress, processingMethod);
    }
    
    // XMLHttpRequest for upload progress tracking
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      
      // Track progress if callback provided
      if (onProgress && typeof onProgress === 'function') {
        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            const percentComplete = Math.round((event.loaded / event.total) * 100);
            onProgress(percentComplete);
          }
        };
      }
      
      xhr.open('POST', `${API_BASE_URL}/upload`);
      
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const response = JSON.parse(xhr.responseText);
            resolve(response);
          } catch (e) {
            reject(new Error('Invalid response format'));
            console.log(e);
          }
        } else {
          reject(new Error(`Upload failed with status: ${xhr.status}`));
        }
      };
      
      xhr.onerror = () => reject(new Error('Network error during upload'));
      xhr.ontimeout = () => reject(new Error('Upload timed out'));
      
      xhr.send(formData);
    });
  } catch (error) {
    console.error('Error uploading PDF:', error);
    throw error;
  }
};

function simulateUpload(file, onProgress, processingMethod) {
  return new Promise((resolve) => {
    let progress = 0;
    const interval = setInterval(() => {
      progress += 10;
      
      if (onProgress) {
        onProgress(progress);
      }
      
      if (progress >= 100) {
        clearInterval(interval);
        
        setTimeout(() => {
          resolve({
            fileId: Date.now() + Math.random().toString(36).substring(2, 10),
            filename: file.name,
            size: file.size,
            data: {
              pages: Math.floor(Math.random() * 20) + 1,
              processed: true,
              method: processingMethod  // Ensure this is included 
            }
          });
        }, 500);
      }
    }, 300);
  });
}

export const sendMessage = async (message, fileIds) => {
  try {
    // For testing while backend is not available
    if (!API_BASE_URL.startsWith('http://localhost')) {
      return simulateMessage(message, fileIds);
    }
    
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        fileIds,
      }),
    });

    if (!response.ok) {
      throw new Error(`Chat query failed with status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error sending message:', error);
    throw error;
  }
};

function simulateMessage(message, fileIds) {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        text: `This is a simulated response to: "${message}". I've analyzed the contents of ${fileIds.length} document(s) and found relevant information that might help answer your question.`,
        sources: fileIds.map(id => ({
          fileId: id,
          title: `Document ${id.substring(0, 6)}`,
          page: Math.floor(Math.random() * 10) + 1
        }))
      });
    }, 1500);
  });
}

export const getUploadedFiles = async () => {
  try {
    // For testing while backend is not available
    if (!API_BASE_URL.startsWith('http://localhost')) {
      return simulateGetFiles();
    }
    
    const response = await fetch(`${API_BASE_URL}/files`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch files with status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching files:', error);
    throw error;
  }
};


function simulateGetFiles() {
  return Promise.resolve([]);
}

export const deleteFile = async (fileId) => {
  try {
    // For testing while backend is not available
    if (!API_BASE_URL.startsWith('http://localhost')) {
      return simulateDeleteFile(fileId);
    }
    
    // Add a check for valid fileId
    if (!fileId) {
      throw new Error("Invalid file ID provided");
    }
    
    // Log the request for debugging
    console.log(`Attempting to delete file with ID: ${fileId}`);
    
    const response = await fetch(`${API_BASE_URL}/files/${fileId}`, {
      method: 'DELETE',
    });
    
    // Improved error handling
    if (response.status === 404) {
      console.warn(`File with ID ${fileId} not found on server, removing from UI only`);
      // Return success even if the file wasn't on the server
      // This allows the UI to clean up even if backend state is inconsistent
      return {
        success: true,
        fileId: fileId,
        message: 'File removed from UI (not found on server)',
        notFoundOnServer: true
      };
    }
    
    if (!response.ok) {
      throw new Error(`Failed to delete file with status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error deleting file:', error);
    throw error;
  }
};

function simulateDeleteFile(fileId) {
  return Promise.resolve({
    success: true,
    fileId: fileId,
    message: 'File successfully deleted'
  });
}