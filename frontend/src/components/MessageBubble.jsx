import './MessageBubble.css';

function MessageBubble({ message }) {
  const { sender, text, timestamp, sources } = message;
  
  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };
  
  return (
    <div className={`message-bubble ${sender}`}>
      <div className="message-avatar">
        {sender === 'user' ? (
          <div className="avatar user-avatar">
            <span>U</span>
          </div>
        ) : sender === 'system' ? (
          <div className="avatar system-avatar">
            <span>S</span>
          </div>
        ) : (
          <div className="avatar ai-avatar">
            <span>AI</span>
          </div>
        )}
      </div>
      
      <div className="message-content">
        <div className="message-text">
          {text.split('\n').map((line, i) => (
            <p key={i}>{line}</p>
          ))}
          
          {sources && sources.length > 0 && (
            <div className="message-sources">
              <div className="sources-title">Sources:</div>
              <ul className="sources-list">
                {sources.map((source, index) => (
                  <li key={index} className="source-item">
                    <svg viewBox="0 0 24 24" width="16" height="16">
                      <path fill="currentColor" d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z" />
                    </svg>
                    <span>{source.title}</span>
                    {source.page && <span className="page-number">p.{source.page}</span>}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
        
        <div className="message-timestamp">
          {formatTimestamp(timestamp)}
        </div>
      </div>
    </div>
  );
}

export default MessageBubble;