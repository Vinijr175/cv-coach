import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Matches.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export default function Matches({ resumeId }) {
  const [resume, setResume] = useState(null);
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!resumeId) return;
    const fetchData = async () => {
      setLoading(true);
      try {
        const resumeResp = await axios.get(`${API_URL}/api/resume/${resumeId}`);
        setResume(resumeResp.data);
        const matchesResp = await axios.get(`${API_URL}/api/resume/${resumeId}/matches?top=10`);
        setMatches(matchesResp.data.matches || []);
      } catch (err) {
        setError(err.response?.data?.detail || err.message);
      } finally {
        setLoading(false);
      }
    };
    const interval = setInterval(fetchData, 2000);
    fetchData();
    return () => clearInterval(interval);
  }, [resumeId]);

  if (loading && !resume) return <p className="loading">Loading...</p>;
  if (error) return <p className="error">Error: {error}</p>;

  return (
    <div className="matches-container">
      {resume && (
        <div className="resume-section">
          <h3>📄 Resume</h3>
          <div className="status-bar">
            <span className={`badge ${resume.status}`}>{resume.status}</span>
          </div>
          {resume.parsed?.error ? (
            <div className="error-box">{resume.parsed.error}</div>
          ) : (
            <div className="resume-info">
              {resume.parsed?.name && (
                <>
                  <p><strong>Name:</strong> {resume.parsed.name}</p>
                  <p><strong>Email:</strong> {resume.parsed.email}</p>
                  <p><strong>Location:</strong> {resume.parsed.location || 'N/A'}</p>
                </>
              )}
              <details>
                <summary>View Full JSON</summary>
                <pre className="json-view">{JSON.stringify(resume.parsed, null, 2)}</pre>
              </details>
            </div>
          )}
        </div>
      )}
      <div className="matches-section">
        <h3>🎯 Job Matches</h3>
        {!resume || resume.status === 'parsing' ? (
          <p className="info">Processing resume...</p>
        ) : matches.length === 0 ? (
          <p className="info">No matches yet</p>
        ) : (
          matches.map((m) => (
            <div key={m.job_id} className="match-card">
              <div className="match-header">
                <span className="score">{m.score}%</span>
                <div>
                  <p className="job-title">{m.job_title}</p>
                  <p className="company">{m.company}</p>
                </div>
              </div>
              <p className="location">📍 {m.location}</p>
              <p className="explanation">{m.explanation}</p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
