import { useState } from 'react';
import { useFileContext } from '../context/FileContext';
import './ProcessingMethodSelector.css';

function ProcessingMethodSelector() {
  const { processingMethod, setProcessingMethod } = useFileContext();
  const [isOpen, setIsOpen] = useState(false);
  
  const methods = [
    {
      id: 'standard',
      name: 'Standard',
      description: 'Basic text extraction and character-based chunking.',
      icon: '📄'
    },
    {
      id: 'semantic',
      name: 'Semantic',
      description: 'Structure-aware extraction with semantic chunking.',
      icon: '📑'
    },
    {
      id: 'layout',
      name: 'Layout',
      description: 'Advanced layout detection with OCR and visual analysis.',
      icon: '📊'
    }
  ];
  
  const handleSelectMethod = (methodId) => {
    setProcessingMethod(methodId);
    console.log(`Processing method changed to: ${methodId}`);
    setIsOpen(false);
  };
  
  const currentMethod = methods.find(m => m.id === processingMethod) || methods[0];
  
  return (
    <div className="processing-method-selector">
      <div className="method-label">Processing Method:</div>
      <div className="method-dropdown">
        <button 
          className="selected-method" 
          onClick={() => setIsOpen(!isOpen)}
        >
          <span className="method-icon">{currentMethod.icon}</span>
          <span className="method-name">{currentMethod.name}</span>
          <span className="dropdown-arrow">▼</span>
        </button>
        
        {isOpen && (
          <div className="method-options">
            {methods.map((method) => (
              <div 
                key={method.id}
                className={`method-option ${method.id === processingMethod ? 'active' : ''}`}
                onClick={() => handleSelectMethod(method.id)}
              >
                <div className="method-option-header">
                  <span className="method-icon">{method.icon}</span>
                  <span className="method-name">{method.name}</span>
                </div>
                <p className="method-description">{method.description}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default ProcessingMethodSelector;