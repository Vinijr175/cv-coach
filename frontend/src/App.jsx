import React, { useState } from 'react';
import Upload from './components/Upload';
import Matches from './components/Matches';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export default function App() {
  const [resumeId, setResumeId] = useState(null);
  const [userEmail, setUserEmail] = useState('demo@example.com');

  return (
    <div className="app">
      <header className="header">
        <h1>🎓 CV Coach</h1>
        <p>AI-powered career coaching: Upload resume, get matched with jobs</p>
      </header>
      <div className="container">
        <section className="section">
          <h2>Step 1: Upload Your Resume</h2>
          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block' }}>
              Email: 
              <input type="email" value={userEmail} onChange={(e) => setUserEmail(e.target.value)} style={{ marginLeft: '10px', padding: '8px', width: '250px' }} />
            </label>
          </div>
          <Upload userEmail={userEmail} onResumeUploaded={setResumeId} />
        </section>
        <hr />
        <section className="section">
          <h2>Step 2: View Results</h2>
          {resumeId ? <Matches resumeId={resumeId} /> : <p style={{ color: '#666' }}>Upload a resume first</p>}
        </section>
      </div>
      <footer className="footer">
        <p>API: {API_URL}</p>
      </footer>
    </div>
  );
}
