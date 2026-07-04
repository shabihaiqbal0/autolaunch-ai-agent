import { useState } from 'react';

function App() {
  const [prompt, setPrompt] = useState('');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      });

      const data = await response.json();
      setResult(data.result || 'No response');
    } catch (error) {
      setResult('Request failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ fontFamily: 'sans-serif', maxWidth: 800, margin: '2rem auto', padding: '1rem' }}>
      <h1>DevLaunch AI</h1>
      <p>Prepare your AI project workflow with a modular backend and React frontend.</p>
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        rows={6}
        placeholder="Describe the project you want to build..."
        style={{ width: '100%', padding: '0.75rem' }}
      />
      <button onClick={handleGenerate} disabled={loading} style={{ marginTop: '1rem', padding: '0.75rem 1rem' }}>
        {loading ? 'Generating...' : 'Generate'}
      </button>
      <pre style={{ whiteSpace: 'pre-wrap', marginTop: '1rem', background: '#f5f5f5', padding: '1rem' }}>
        {result}
      </pre>
    </div>
  );
}

export default App;
