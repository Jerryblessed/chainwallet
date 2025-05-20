import React, { useEffect, useState } from 'react';
import { HashRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import './App.css';
import './scrollbar.css';
import NavBar from './components/NavBar';
import cardData from './CardData.json';
import Nodes from './components/Nodes';
import SettingsModal from './components/SettingsModal';
import FaucetModal from './components/FaucetModal';
import WalletModal from './components/WalletModal';
import FastWithdrawalModal from './components/FastWithdrawalModal';
import WelcomeModal from './components/WelcomeModal';
import QuoteWidget from './components/QuoteWidget';
import ShutdownModal from './components/ShutdownModal';
import DownloadInProgressModal from './components/DownloadInProgressModal';
import { ThemeProvider, useTheme } from './contexts/ThemeContext';

// Error Boundary to catch runtime errors
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error('Uncaught error:', error, info);
  }

  render() {
    
      if (this.state.hasError) {
        return (
          <div className="flex flex-col items-center justify-start min-h-screen bg-gray-50 p-6">
            <h1 className="text-4xl font-bold text-red-600 mb-6">🚨 Something went wrong</h1>

            <div className="w-full max-w-2xl bg-white border-l-4 border-red-600 shadow-md p-6 mb-6">
              <h2 className="text-2xl font-semibold text-red-600 mb-2">Error Details:</h2>
              <pre className="bg-gray-100 rounded p-4 overflow-x-auto text-sm">
                {this.state.error?.toString()}
              </pre>
            </div>

            <div className="w-full max-w-2xl bg-yellow-50 border-l-4 border-yellow-400 shadow-md p-6">
              <h3 className="text-xl font-semibold text-yellow-800 mb-2">Possible Solutions:</h3>
              <ul className="list-disc list-inside space-y-2 text-gray-700">
                <li>
                  Run inside Electron or guard your calls with{' '}
                  <code className="bg-gray-200 px-1 rounded">window.electronAPI</code>.
                </li>
                <li>
                  Ensure your <code className="bg-gray-200 px-1 rounded">preload.js</code> uses{' '}
                  <code className="bg-gray-200 px-1 rounded">contextBridge.exposeInMainWorld</code>.
                </li>
                <li>
                  If you’re using ES modules, make sure your <code className="bg-gray-200 px-1 rounded">
                    package.json
                  </code> has <code className="italic">"type": "module"</code>.
                </li>
                <li>
                  Set up the Chrome sandbox on Linux:
                  <a
                    href="https://www.electronjs.org/docs/latest/tutorial/sandbox#linux"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 underline"
                  >
                    Official Electron Sandbox Docs
                  </a>
                </li>
                <li>
                  Read more on Electron’s context isolation:{' '}
                  <a
                    href="https://www.electronjs.org/docs/latest/tutorial/context-isolation"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 underline"
                  >
                    Context Isolation Docs
                  </a>
                </li>
              </ul>
            </div>
          </div>
        );
      }
      return this.props.children;
    }
      }


function AppContent() {
  const { isDarkMode } = useTheme();
  const dispatch = useDispatch();
  const [showWelcomeModal, setShowWelcomeModal] = useState(false);
  const [activeDownloads, setActiveDownloads] = useState([]);
  const [showDownloadModal, setShowDownloadModal] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);

  // Expose cardData globally
  useEffect(() => {
    window.cardData = cardData;
  }, []);

  // Apply theme
  useEffect(() => {
    document.body.className = isDarkMode ? 'dark' : 'light';
  }, [isDarkMode]);

  // Initialization and downloads listener
  useEffect(() => {
    if (!window.electronAPI) {
      console.warn('electronAPI not found - running in web mode');
      setIsInitialized(true);
      return;
    }
    const unsubscribe = window.electronAPI.onDownloadsInProgress(downloads => {
      setActiveDownloads(downloads);
      setShowDownloadModal(true);
    });
    (async () => {
      try {
        const result = await window.electronAPI.getMasterWallet();
        if (!result.success || !result.data) setShowWelcomeModal(true);
      } catch {
        setShowWelcomeModal(true);
      } finally {
        setIsInitialized(true);
        window.electronAPI.notifyReady();
      }
    })();
    return () => unsubscribe();
  }, [dispatch]);

  const handleForceQuit = () => {
    if (window.electronAPI) window.electronAPI.forceQuitWithDownloads();
  };

  if (!isInitialized) return null;

  return (
    <Router>
      <div className="App">
        <NavBar />
        <Routes>
          <Route path="/" element={<Navigate to="/chains" replace />} />
          <Route path="/chains" element={<Nodes />} />
          <Route path="/wallet" element={<WalletModal />} />
          <Route path="/fast-withdrawal" element={<FastWithdrawalModal />} />
        </Routes>
        <FaucetModal />
        <SettingsModal onResetComplete={() => setShowWelcomeModal(true)} />
        <WelcomeModal isOpen={showWelcomeModal} onClose={() => setShowWelcomeModal(false)} />
        <QuoteWidget />
        <ShutdownModal />
        <DownloadInProgressModal
          downloads={activeDownloads}
          onClose={() => setShowDownloadModal(false)}
          onForceQuit={handleForceQuit}
          isOpen={showDownloadModal}
        />
      </div>
    </Router>
  );
}

function App() {
  return (
    <ThemeProvider>
      <ErrorBoundary>
        <AppContent />
      </ErrorBoundary>
    </ThemeProvider>
  );
}

export default App;
