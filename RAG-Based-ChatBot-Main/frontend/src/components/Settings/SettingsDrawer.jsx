import React from "react";

export default function SettingsDrawer({
  isOpen,
  onClose,
  topK,
  setTopK,
  scoreThreshold,
  setScoreThreshold,
  fusionMethod,
  setFusionMethod,
  fusionAlpha,
  setFusionAlpha,
  routerMode,
  setRouterMode,
  temperature,
  setTemperature,
  llmModel = "Qwen 2.5 3B",
  embeddingModel = "nomic-embed-text:v1.5"
}) {
  if (!isOpen) return null;

  return (
    <div className="settings-drawer-backdrop" onClick={onClose}>
      <aside className="chatgpt-settings-drawer" onClick={(e) => e.stopPropagation()}>
        <div className="settings-drawer-header">
          <div className="settings-header-title">
            <span className="settings-gear-icon">⚙️</span>
            <h3>RAG Engine Settings</h3>
          </div>
          <button className="btn-close-settings" onClick={onClose} title="Close Settings">
            ✕
          </button>
        </div>

        <div className="settings-drawer-scroll-body">
          {/* Models Information */}
          <div className="settings-card-group">
            <h4 className="group-title">Engine Architecture</h4>
            <div className="info-stat-row">
              <span className="stat-label">LLM Model:</span>
              <span className="stat-badge">{llmModel} (Ollama Local)</span>
            </div>
            <div className="info-stat-row">
              <span className="stat-label">Embedding Model:</span>
              <span className="stat-badge">{embeddingModel}</span>
            </div>
            <div className="info-stat-row">
              <span className="stat-label">Vector Database:</span>
              <span className="stat-badge">Qdrant Local (doc_chunks)</span>
            </div>
            <div className="info-stat-row">
              <span className="stat-label">Streaming Protocol:</span>
              <span className="stat-badge">FastAPI Async WebSockets</span>
            </div>
          </div>

          {/* Retrieval Tuning */}
          <div className="settings-card-group">
            <h4 className="group-title">Retrieval & Reranking</h4>

            <div className="setting-control-item">
              <div className="control-label-row">
                <label>Top-K Chunks:</label>
                <span className="control-val">{topK}</span>
              </div>
              <input
                type="range"
                className="pro-range-slider"
                min={1}
                max={20}
                value={topK}
                onChange={(e) => setTopK(parseInt(e.target.value, 10))}
              />
            </div>

            <div className="setting-control-item">
              <div className="control-label-row">
                <label>Similarity Threshold:</label>
                <span className="control-val">{scoreThreshold.toFixed(2)}</span>
              </div>
              <input
                type="range"
                className="pro-range-slider"
                min={0.0}
                max={0.9}
                step={0.05}
                value={scoreThreshold}
                onChange={(e) => setScoreThreshold(parseFloat(e.target.value))}
              />
            </div>

            <div className="setting-control-item">
              <label className="select-label">Hybrid Fusion Method:</label>
              <select
                className="pro-select-dropdown"
                value={fusionMethod}
                onChange={(e) => setFusionMethod(e.target.value)}
              >
                <option value="rrf">Reciprocal Rank Fusion (RRF k=60)</option>
                <option value="weighted">Weighted Linear Sum</option>
                <option value="dense_only">Dense Vector Only</option>
                <option value="bm25_only">Sparse BM25 Only</option>
              </select>
            </div>

            {fusionMethod === "weighted" && (
              <div className="setting-control-item">
                <div className="control-label-row">
                  <label>Dense Alpha Weight:</label>
                  <span className="control-val">{fusionAlpha.toFixed(2)}</span>
                </div>
                <input
                  type="range"
                  className="pro-range-slider"
                  min={0.0}
                  max={1.0}
                  step={0.05}
                  value={fusionAlpha}
                  onChange={(e) => setFusionAlpha(parseFloat(e.target.value))}
                />
              </div>
            )}
          </div>

          {/* Model Generation Tuning */}
          <div className="settings-card-group">
            <h4 className="group-title">Generation Parameters</h4>

            <div className="setting-control-item">
              <label className="select-label">Routing Mode:</label>
              <select
                className="pro-select-dropdown"
                value={routerMode}
                onChange={(e) => setRouterMode(e.target.value)}
              >
                <option value="hybrid">Hybrid (Fast Rules + LLM Router)</option>
                <option value="rules_only">Fast Keyword Rules Only</option>
                <option value="force_doc">Force Document Grounding</option>
                <option value="force_gen">Force General Reasoning</option>
              </select>
            </div>

            <div className="setting-control-item">
              <div className="control-label-row">
                <label>Temperature:</label>
                <span className="control-val">{temperature.toFixed(2)}</span>
              </div>
              <input
                type="range"
                className="pro-range-slider"
                min={0.0}
                max={1.0}
                step={0.05}
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
              />
            </div>
          </div>
        </div>

        <div className="settings-drawer-footer">
          <button className="btn-save-settings" onClick={onClose}>
            Done
          </button>
        </div>
      </aside>
    </div>
  );
}
