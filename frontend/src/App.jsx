
import { useState, useRef } from "react";
import "./App.css";

const API_BASE = "http://localhost:5000/api";

export default function App() {
  const [question, setQuestion] = useState("");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const sceneRef = useRef(null);

  function handleMouseMove(event) {
    if (!sceneRef.current) return;

    const rect = sceneRef.current.getBoundingClientRect();

    const x = (event.clientX - rect.left) / rect.width - 0.5;
    const y = (event.clientY - rect.top) / rect.height - 0.5;

    sceneRef.current.style.setProperty("--mouse-x", `${x * 22}px`);
    sceneRef.current.style.setProperty("--mouse-y", `${y * 22}px`);
  }

  function handleMouseLeave() {
    if (!sceneRef.current) return;

    sceneRef.current.style.setProperty("--mouse-x", "0px");
    sceneRef.current.style.setProperty("--mouse-y", "0px");
  }


  const suggestions = [
    "Does AI improve early disease diagnosis?",
    "Are electric vehicles better for the environment?",
    "How does social media affect mental health?",
  ];

  async function startResearch(value = question) {
    const trimmed = value.trim();
    if (!trimmed) return;

    setLoading(true);
    setError(null);
    setResults(null);

    try {
      console.log("[TRACE] Sending research request:", { question: trimmed, max_results: 10 });

      const response = await fetch(`${API_BASE}/research`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmed, max_results: 10 }),
      });

      console.log("[TRACE] Response status:", response.status);

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.error || `Research failed (${response.status})`);
      }

      const data = await response.json();
      console.log("[TRACE] Research results:", data);
      setResults(data);
    } catch (err) {
      console.error("[TRACE] Research error:", err.message);
      setError(err.message || "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="trace-page">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />
      <div className="grain" />

      <header className="topbar">
        <a className="brand" href="#home" aria-label="TRACE home">
          <span className="brand-mark">
            <span />
          </span>
          <span>TRACE</span>
        </a>

        <nav className="navigation">
          <a className="nav-active" href="#home">Home</a>
          <a href="#research">Research</a>
          <a href="#about">About</a>
        </nav>

        <div className="edition">VYUHAM ’26</div>
      </header>

      <section className="hero" id="home">
        <div className="side-label">
          <span>RESEARCH INTELLIGENCE</span>
          <i />
        </div>

        <div
  className="orbital-scene"
  ref={sceneRef}
  onMouseMove={handleMouseMove}
  onMouseLeave={handleMouseLeave}
  aria-hidden="true"
>
          <div className="orbital orbital-one">
            <span className="orbit-node node-one" />
          </div>
          <div className="orbital orbital-two">
            <span className="orbit-node node-two" />
          </div>
          <div className="orbital orbital-three">
            <span className="orbit-node node-three" />
          </div>

          <div className="orb-glow" />
          <div className="orb">
            <div className="orb-highlight" />
            <div className="orb-wave wave-one" />
            <div className="orb-wave wave-two" />
          </div>

          <span className="scene-particle particle-one" />
          <span className="scene-particle particle-two" />
          <span className="scene-particle particle-three" />
        </div>

        <div className="hero-copy">
          <p className="eyebrow">
            <span /> BETTER QUESTIONS. REAL EVIDENCE.
          </p>

          <h1>
            Trace what
            <br />
            <span>matters.</span>
          </h1>

          <p className="hero-description">
            Explore multiple perspectives, verify claims,
            and discover what the evidence actually says.
          </p>
        </div>

        <form
          className="research-form"
          id="research"
          onSubmit={(event) => {
            event.preventDefault();
            startResearch();
          }}
        >
          <span className="search-symbol" aria-hidden="true" />
          <input
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="What do you want to investigate?"
            aria-label="Research question"
          />
          <button type="submit" aria-label="Begin research">
            <span>↗</span>
          </button>
        </form>

        <div className="suggestions">
          <p className="suggestion-heading">
            <span /> Try asking:
          </p>
          <div className="suggestion-list">
            {suggestions.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                onClick={() => setQuestion(suggestion)}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>

        <div className="process-steps">
          <div><span>01</span><small>DISCOVER</small></div>
          <div><span>02</span><small>VERIFY</small></div>
          <div><span>03</span><small>COMPARE</small></div>
        </div>
      </section>

      {loading && (
        <div className="results-loading">
          <p>Researching…</p>
        </div>
      )}

      {error && (
        <div className="results-error">
          <p>{error}</p>
          {error.includes("fetch") || error.includes("Failed to fetch") || error.includes("network") ? (
            <p className="connection-hint">
              Backend not running. Start it with:<br />
              <code>cd backend && python app.py</code>
            </p>
          ) : null}
        </div>
      )}

      {results && !loading && !error && (
        <section className="results-section">
          <div className="results-header">
            <h2>Research Results</h2>
            <p className="results-question">“{results.question}”</p>
            <p className="results-id">Research ID: {results.research_id}</p>
          </div>

          {results.sources && results.sources.length > 0 ? (
            <div className="sources-grid">
              {results.sources.map((source) => (
                <div key={source.source_id} className="source-card">
                  <div className="source-meta">
                    <span className="source-id">{source.source_id}</span>
                    <span className="source-relevance">
                      Relevance: {source.relevance?.score ?? "N/A"}
                    </span>
                  </div>
                  <h3 className="source-title">{source.title}</h3>
                  <div className="source-details">
                    <span className="source-authors">
                      {source.authors?.join(", ") || "Unknown authors"}
                    </span>
                    <span className="source-year">
                      {source.publication_year || "n.d."}
                    </span>
                    <span className="source-journal">
                      {source.journal || "Unknown journal"}
                    </span>
                  </div>
                  <p className="source-abstract">
                    {source.snippet || source.abstract || ""}
                  </p>
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="source-link"
                  >
                    View Source →
                  </a>
                </div>
              ))}
            </div>
          ) : (
            <div className="results-empty">
              <p>No sources found for this question.</p>
            </div>
          )}
        </section>
      )}

      <footer className="footer">
        <a href="#research" className="scroll-link">
          <span className="scroll-icon">↓</span>
          SCROLL TO EXPLORE
        </a>

        <p>SCIENTIFIC <i /> MULTI-SOURCE <i /> EVIDENCE-LED</p>
      </footer>
    </main>
  );
}
