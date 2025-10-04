import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [backendStatus, setBackendStatus] = useState('Checking...');

  useEffect(() => {
    const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    
    const checkBackend = async () => {
      try {
        const response = await fetch(`${apiUrl}/health`);
        if (response.ok) {
          setBackendStatus('✅ Connected');
        } else {
          setBackendStatus('⚠️ Backend Error');
        }
      } catch (error) {
        setBackendStatus('❌ Not Connected');
      } finally {
        setIsLoading(false);
      }
    };

    checkBackend();
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>🍳 Kitchen Management</h1>
        <p className="subtitle">מערכת ניהול מטבחים</p>
        
        <div className="status-card">
          <h2>System Status</h2>
          <div className="status-line">
            <span>Frontend:</span>
            <span className="status-badge success">✅ Active</span>
          </div>
          <div className="status-line">
            <span>Backend:</span>
            <span className={`status-badge ${isLoading ? 'loading' : backendStatus.includes('✅') ? 'success' : 'error'}`}>
              {isLoading ? '⏳ Loading...' : backendStatus}
            </span>
          </div>
        </div>

        <div className="info-card">
          <h3>🎉 Welcome!</h3>
          <p>המערכת עלתה בהצלחה על Railway</p>
          <p className="version">Version: 1.0.0 - Demo</p>
        </div>

        <button className="test-button" onClick={() => alert('System is running!')}>
          🚀 Test System
        </button>
      </header>
    </div>
  );
}

export default App;
