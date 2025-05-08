import './App.css';
import Header from './components/Header';
import DocumentSidebar from './components/DocumentSidebar';
import ChatInterface from './components/ChatInterface';
import { FileProvider } from './context/FileContext';
import { ChatProvider } from './context/ChatContext';

function App() {
  return (
    <div className="app-container">
      <FileProvider>
        <ChatProvider>
          <Header />
          
          <main className="main-content">
            <DocumentSidebar />
            <ChatInterface />
          </main>
        </ChatProvider>
      </FileProvider>
    </div>
  );
}

export default App;