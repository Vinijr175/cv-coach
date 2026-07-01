import React, { useState } from 'react';
import axios from 'axios';
import './Upload.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export default function Upload({ userEmail, onResumeUploaded }) {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleUpload = async () => {
    if (!file) { setError('Select file'); return; }
    if (!userEmail) { setError('Enter email'); return; }
    setLoading(true);
    setStatus('Uploading...');
    try {
      const form = new FormData();
      form.append('file', file);
      form.append('user_email', userEmail);
      const resp = await axios.post(`${API_URL}/api/upload-resume`, form);
      setStatus(`✓ Uploaded (ID: ${resp.data.resume_id})`);
      onResumeUploaded(resp.data.resume_id);
      setFile(null);
    } catch (err) {
      setError(`✗ Failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="upload-container">
      <div className="upload-box">
        <input type="file" onChange={(e) => { setFile(e.target.files?.[0]); setError(null); }} disabled={loading} />
        {file && <p className="file-name">✓ {file.name}</p>}
      </div>
      <button onClick={handleUpload} disabled={!file || loading} className="upload-btn">
        {loading ? '⏳ Processing...' : '📤 Upload'}
      </button>
      {status && <p className="status success">{status}</p>}
      {error && <p className="status error">{error}</p>}
    </div>
  );
}
