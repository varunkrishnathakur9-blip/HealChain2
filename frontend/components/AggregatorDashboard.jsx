import React, { useEffect, useState } from 'react';

const AggregatorDashboard = ({ user }) => {
  const [status, setStatus] = useState('idle');
  const [results, setResults] = useState(null);

  useEffect(() => {
    const t = setInterval(async () => {
      try {
        const res = await fetch('http://127.0.0.1:5000/status');
        if (res.ok) {
          const d = await res.json();
          setStatus(d.status);
        }
      } catch (e) {}
    }, 3000);
    return () => clearInterval(t);
  }, []);

  const fetchResults = async () => {
    try {
      const r = await fetch('http://127.0.0.1:5000/results');
      const data = await r.json();
      if (data.found) setResults(data.results);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div style={{ padding: 24 }}>
      <h2>Aggregator Dashboard</h2>
      <p>Signed in as <strong>{user?.name || user?.email}</strong></p>
      <p>Aggregator access: showing simulation state and candidate info.</p>
      <p>Simulation status: <strong>{status}</strong></p>
      <div style={{ marginTop: 12 }}>
        <button onClick={fetchResults} style={{ padding: '8px 12px' }}>Fetch Results</button>
      </div>

      {results && (
        <div style={{ marginTop: 12 }}>
          <h4>Candidate Block</h4>
          <pre style={{ background: '#f5f5f5', padding: 12 }}>{JSON.stringify(results.candidate_block || results.candidateBlock || results, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default AggregatorDashboard;
