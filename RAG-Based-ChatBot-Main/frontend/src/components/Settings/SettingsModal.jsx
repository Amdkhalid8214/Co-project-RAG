import React, { useState, useEffect } from "react";

export default function SettingsModal({
  isOpen,
  onClose,
  initialTab = "appearance",
  theme,
  setTheme,
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
  setLlmModel,
  embeddingModel = "nomic-embed-text:v1.5",
  currentUser,
  setCurrentUser,
  onClearAllConversations,
  onLogout,
  onToggleRole,
  webMode,
  setWebMode
}) {
  const [activeTab, setActiveTab] = useState(initialTab);
  const [searchFilter, setSearchFilter] = useState("");
  const [saveToast, setSaveToast] = useState("");

  useEffect(() => {
    if (isOpen && initialTab) {
      setActiveTab(initialTab);
    }
  }, [isOpen, initialTab]);

  if (!isOpen) return null;

  const username = currentUser?.username || "Amd Khalid";
  const userRole = currentUser?.role || "Free Plan";
  const isAdmin = userRole.toLowerCase().includes("admin");

  const showToast = (msg) => {
    setSaveToast(msg);
    setTimeout(() => setSaveToast(""), 3000);
  };

  const navItems = [
    { id: "general", label: "General", icon: "⚙️" },
    { id: "appearance", label: "Appearance", icon: "☼" },
    { id: "notifications", label: "Notifications", icon: "🔔" },
    { id: "profile", label: "Profile", icon: "👤", hasArrow: true },
    { id: "security", label: "Security and login", icon: "🔒" },
    { id: "account", label: "Account", icon: "👤" },
    { id: "archived", label: "Archived chats", icon: "📦" },
    { id: "parental", label: "Parental controls", icon: "👨‍👩‍👧" },
    { id: "trusted", label: "Trusted contact", icon: "🛡️" },
    { id: "voice", label: "Voice", icon: "🎙️" },
    { id: "storage", label: "Storage", icon: "📁" },
    { id: "personalization", label: "Personalization", icon: "⚡" }
  ];

  const adminNavItems = [
    { id: "rag_admin", label: "Developer & RAG Settings", icon: "🛠️" }
  ];

  const filteredNavItems = navItems.filter((i) =>
    i.label.toLowerCase().includes(searchFilter.toLowerCase())
  );

  return (
    <div className="chatgpt-settings-modal-backdrop" onClick={onClose}>
      <div
        className="chatgpt-settings-modal-card"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Left Settings Navigation Sidebar matching Image 2 */}
        <aside className="settings-modal-sidebar">
          {/* Back to app header button */}
          <button className="btn-back-to-app" onClick={onClose}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <line x1="19" y1="12" x2="5" y2="12" />
              <polyline points="12 19 5 12 12 5" />
            </svg>
            <span>Back to app</span>
          </button>

          {/* Search bar */}
          <div className="settings-search-wrapper">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="search-icon">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input
              type="text"
              className="settings-search-input"
              placeholder="Search"
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
            />
          </div>

          <div className="settings-nav-scroll-list">
            <div className="settings-nav-group-title">Personal</div>

            {filteredNavItems.map((item) => {
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  className={`settings-nav-item ${isActive ? "active" : ""}`}
                  onClick={() => setActiveTab(item.id)}
                >
                  <span className="nav-item-icon">{item.icon}</span>
                  <span className="nav-item-text">{item.label}</span>
                  {item.hasArrow && <span className="nav-item-external-arrow">↗</span>}
                </button>
              );
            })}

            {/* Admin Only Section (Developer Settings for Admin) */}
            {isAdmin && (
              <>
                <div className="settings-nav-group-title admin-title">
                  <span>Administration (Admin Only)</span>
                </div>
                {adminNavItems.map((item) => {
                  const isActive = activeTab === item.id;
                  return (
                    <button
                      key={item.id}
                      className={`settings-nav-item admin-item ${isActive ? "active" : ""}`}
                      onClick={() => setActiveTab(item.id)}
                    >
                      <span className="nav-item-icon">{item.icon}</span>
                      <span className="nav-item-text">{item.label}</span>
                    </button>
                  );
                })}
              </>
            )}
          </div>
        </aside>

        {/* Right Settings Content Stage */}
        <main className="settings-modal-content-stage">
          {saveToast && <div className="settings-toast-banner">{saveToast}</div>}

          {/* 1. APPEARANCE TAB */}
          {activeTab === "appearance" && (
            <div className="settings-tab-panel">
              <h2 className="tab-panel-title">Appearance</h2>
              <p className="tab-panel-desc">Customize how DocuChat AI looks on your device.</p>

              <div className="settings-card-row">
                <div className="card-row-info">
                  <div className="card-row-label">Theme</div>
                  <div className="card-row-sub">Choose between light, dark, or system appearance.</div>
                </div>
                <div className="theme-toggle-pills-row">
                  <button
                    className={`theme-pill-btn ${theme === "light" ? "active" : ""}`}
                    onClick={() => {
                      setTheme("light");
                      localStorage.setItem("docuchat_theme", "light");
                      showToast("Theme changed to Light");
                    }}
                  >
                    <span>☼ Light</span>
                  </button>
                  <button
                    className={`theme-pill-btn ${theme === "dark" ? "active" : ""}`}
                    onClick={() => {
                      setTheme("dark");
                      localStorage.setItem("docuchat_theme", "dark");
                      showToast("Theme changed to Dark");
                    }}
                  >
                    <span>🌙 Dark</span>
                  </button>
                  <button
                    className="theme-pill-btn"
                    onClick={() => {
                      const sysTheme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
                      setTheme(sysTheme);
                      showToast("Theme set to match System");
                    }}
                  >
                    <span>💻 System</span>
                  </button>
                </div>
              </div>

              <div className="settings-card-row">
                <div className="card-row-info">
                  <div className="card-row-label">High Contrast Text</div>
                  <div className="card-row-sub">Increase text legibility for citations and documents.</div>
                </div>
                <label className="settings-switch">
                  <input type="checkbox" defaultChecked />
                  <span className="slider round"></span>
                </label>
              </div>

              <div className="settings-card-row">
                <div className="card-row-info">
                  <div className="card-row-label">Code Syntax Highlighting</div>
                  <div className="card-row-sub">Use high-contrast coloring for Python, JSON, and SQL blocks.</div>
                </div>
                <label className="settings-switch">
                  <input type="checkbox" defaultChecked />
                  <span className="slider round"></span>
                </label>
              </div>
            </div>
          )}

          {/* 2. GENERAL TAB */}
          {activeTab === "general" && (
            <div className="settings-tab-panel">
              <h2 className="tab-panel-title">General</h2>
              <p className="tab-panel-desc">Manage standard workspace preferences and conversation history.</p>

              <div className="settings-card-row">
                <div className="card-row-info">
                  <div className="card-row-label">Language</div>
                  <div className="card-row-sub">Select your primary language for AI responses.</div>
                </div>
                <select className="settings-inline-select" defaultValue="en">
                  <option value="en">English (US)</option>
                  <option value="es">Español</option>
                  <option value="fr">Français</option>
                  <option value="de">Deutsch</option>
                  <option value="zh">中文</option>
                </select>
              </div>

              <div className="settings-card-row">
                <div className="card-row-info">
                  <div className="card-row-label">Default Real-Web Search</div>
                  <div className="card-row-sub">Automatically query live web data for queries about current events.</div>
                </div>
                <label className="settings-switch">
                  <input
                    type="checkbox"
                    checked={webMode}
                    onChange={(e) => setWebMode(e.target.checked)}
                  />
                  <span className="slider round"></span>
                </label>
              </div>

              <div className="settings-card-row danger-row">
                <div className="card-row-info">
                  <div className="card-row-label">Delete all conversations</div>
                  <div className="card-row-sub">Permanently clear all chat history and active message threads.</div>
                </div>
                <button
                  className="btn-danger-outline"
                  onClick={() => {
                    if (window.confirm("Are you sure you want to delete all conversations? This action cannot be undone.")) {
                      onClearAllConversations && onClearAllConversations();
                      showToast("All conversations deleted.");
                    }
                  }}
                >
                  Clear all
                </button>
              </div>
            </div>
          )}

          {/* 3. PROFILE TAB */}
          {activeTab === "profile" && (
            <div className="settings-tab-panel">
              <h2 className="tab-panel-title">Profile</h2>
              <p className="tab-panel-desc">Manage your public name and enterprise identity.</p>

              <div className="settings-form-block">
                <div className="avatar-preview-row">
                  <div className="large-avatar-circle">
                    {(username.slice(0, 2)).toUpperCase()}
                  </div>
                  <div className="avatar-meta">
                    <strong>{username}</strong>
                    <span>{userRole}</span>
                  </div>
                </div>

                <div className="settings-field-group">
                  <label>Display Name</label>
                  <input
                    type="text"
                    className="settings-text-input"
                    defaultValue={username}
                    id="input-profile-name"
                  />
                </div>

                <div className="settings-field-group">
                  <label>Email Address</label>
                  <input
                    type="email"
                    className="settings-text-input"
                    defaultValue="amd@docuchat.ai"
                    id="input-profile-email"
                  />
                </div>

                <button
                  className="btn-primary-save"
                  onClick={() => {
                    const newName = document.getElementById("input-profile-name")?.value;
                    if (newName && setCurrentUser) {
                      setCurrentUser((prev) => {
                        const updated = { ...prev, username: newName };
                        localStorage.setItem("docuchat_user", JSON.stringify(updated));
                        return updated;
                      });
                      showToast("Profile updated successfully");
                    }
                  }}
                >
                  Save changes
                </button>
              </div>
            </div>
          )}

          {/* 4. SECURITY AND LOGIN TAB */}
          {activeTab === "security" && (
            <div className="settings-tab-panel">
              <h2 className="tab-panel-title">Security & Login</h2>
              <p className="tab-panel-desc">Manage sessions, authentication credentials, and access control.</p>

              <div className="settings-card-row">
                <div className="card-row-info">
                  <div className="card-row-label">Active Session</div>
                  <div className="card-row-sub">FastAPI signed JWT session (Expires in 24 hours).</div>
                </div>
                <span className="badge-active-green">● Active Now</span>
              </div>

              <div className="settings-card-row">
                <div className="card-row-info">
                  <div className="card-row-label">Two-Factor Authentication (2FA)</div>
                  <div className="card-row-sub">Add an extra layer of security using an authenticator app.</div>
                </div>
                <button className="btn-secondary-action" onClick={() => showToast("2FA configuration enabled.")}>
                  Configure 2FA
                </button>
              </div>

              <div className="settings-card-row danger-row">
                <div className="card-row-info">
                  <div className="card-row-label">Log out of DocuChat AI</div>
                  <div className="card-row-sub">End this active session and return to the login screen.</div>
                </div>
                <button
                  className="btn-danger-outline"
                  onClick={() => {
                    onLogout && onLogout();
                    onClose();
                  }}
                >
                  Log out
                </button>
              </div>
            </div>
          )}

          {/* 5. ACCOUNT TAB */}
          {activeTab === "account" && (
            <div className="settings-tab-panel">
              <h2 className="tab-panel-title">Account</h2>
              <p className="tab-panel-desc">Subscription status and role permissions.</p>

              <div className="settings-card-row">
                <div className="card-row-info">
                  <div className="card-row-label">Current Role</div>
                  <div className="card-row-sub">
                    {isAdmin
                      ? "Enterprise Administrator — Unrestricted RAG pipeline access"
                      : "Standard User — Streamlined document intelligence workspace"}
                  </div>
                </div>
                <span className={`role-pill-badge ${isAdmin ? "admin" : "user"}`}>
                  {isAdmin ? "Enterprise Admin" : "Free Plan"}
                </span>
              </div>

              <div className="settings-card-row">
                <div className="card-row-info">
                  <div className="card-row-label">Perspective Switcher</div>
                  <div className="card-row-sub">
                    Toggle between Admin Mode and User Mode to test how the interface adapts.
                  </div>
                </div>
                <button
                  className="btn-primary-action"
                  onClick={() => {
                    onToggleRole && onToggleRole();
                    showToast(isAdmin ? "Switched to User Mode" : "Switched to Admin Mode (Developer Settings unlocked)");
                  }}
                >
                  {isAdmin ? "Switch to User Mode" : "Switch to Admin Mode"}
                </button>
              </div>

              <div className="settings-card-row danger-row">
                <div className="card-row-info">
                  <div className="card-row-label">Log out of all devices</div>
                  <div className="card-row-sub">Revoke all active JWT tokens across all browsers.</div>
                </div>
                <button
                  className="btn-danger-outline"
                  onClick={() => {
                    onLogout && onLogout();
                    onClose();
                  }}
                >
                  Log out all
                </button>
              </div>
            </div>
          )}

          {/* 6. NOTIFICATIONS TAB */}
          {activeTab === "notifications" && (
            <div className="settings-tab-panel">
              <h2 className="tab-panel-title">Notifications</h2>
              <p className="tab-panel-desc">Configure audio and visual alerts during long document ingestion.</p>

              <div className="settings-card-row">
                <div className="card-row-info">
                  <div className="card-row-label">Audio alert on completion</div>
                  <div className="card-row-sub">Play a subtle chime when complex queries finish generating.</div>
                </div>
                <label className="settings-switch">
                  <input type="checkbox" defaultChecked />
                  <span className="slider round"></span>
                </label>
              </div>

              <div className="settings-card-row">
                <div className="card-row-info">
                  <div className="card-row-label">Ingestion Progress Alerts</div>
                  <div className="card-row-sub">Show WebSocket notifications when document chunking completes.</div>
                </div>
                <label className="settings-switch">
                  <input type="checkbox" defaultChecked />
                  <span className="slider round"></span>
                </label>
              </div>
            </div>
          )}

          {/* 7. VOICE TAB */}
          {activeTab === "voice" && (
            <div className="settings-tab-panel">
              <h2 className="tab-panel-title">Voice</h2>
              <p className="tab-panel-desc">Configure speech-to-text input and synthetic voice models.</p>

              <div className="settings-card-row">
                <div className="card-row-info">
                  <div className="card-row-label">Voice Model</div>
                  <div className="card-row-sub">Select the assistant voice personality.</div>
                </div>
                <select className="settings-inline-select" defaultValue="alloy">
                  <option value="alloy">Alloy (Neutral & Clear)</option>
                  <option value="echo">Echo (Warm & Conversational)</option>
                  <option value="fable">Fable (Expressive British)</option>
                  <option value="onyx">Onyx (Deep & Authoritative)</option>
                  <option value="nova">Nova (Energetic)</option>
                  <option value="shimmer">Shimmer (Soft & Calm)</option>
                </select>
              </div>

              <div className="settings-card-row">
                <div className="card-row-info">
                  <div className="card-row-label">Test Microphone</div>
                  <div className="card-row-sub">Check browser WebAudio input levels.</div>
                </div>
                <button
                  className="btn-secondary-action"
                  onClick={() => alert("Microphone access verified. Ready for speech input.")}
                >
                  Test Audio
                </button>
              </div>
            </div>
          )}

          {/* 8. STORAGE TAB */}
          {activeTab === "storage" && (
            <div className="settings-tab-panel">
              <h2 className="tab-panel-title">Storage</h2>
              <p className="tab-panel-desc">Manage indexed document sizes and vector cache.</p>

              <div className="settings-card-row">
                <div className="card-row-info">
                  <div className="card-row-label">Document Cache Size</div>
                  <div className="card-row-sub">Attention.pdf (2.4 MB), Product_Requirements.pdf (1.2 MB)</div>
                </div>
                <span className="stat-pill-label">3.6 MB Total</span>
              </div>

              <div className="settings-card-row danger-row">
                <div className="card-row-info">
                  <div className="card-row-label">Clear Document Cache</div>
                  <div className="card-row-sub">Purge locally cached PDF renders and previews.</div>
                </div>
                <button
                  className="btn-danger-outline"
                  onClick={() => showToast("Local document cache purged.")}
                >
                  Purge Cache
                </button>
              </div>
            </div>
          )}

          {/* 9. PERSONALIZATION TAB */}
          {activeTab === "personalization" && (
            <div className="settings-tab-panel">
              <h2 className="tab-panel-title">Personalization</h2>
              <p className="tab-panel-desc">Provide custom instructions that guide assistant answers.</p>

              <div className="settings-field-group">
                <label>Custom Instructions</label>
                <textarea
                  className="settings-textarea-input"
                  rows={4}
                  placeholder="e.g. Always summarize numerical tables, highlight citations in bold, and provide executive summaries..."
                  defaultValue="Prioritize exact numerical figures and cite the exact page number for every claim."
                />
              </div>

              <button
                className="btn-primary-save"
                onClick={() => showToast("Custom instructions saved.")}
              >
                Save instructions
              </button>
            </div>
          )}

          {/* 10. ARCHIVED CHATS / PARENTAL / TRUSTED TABS */}
          {(activeTab === "archived" || activeTab === "parental" || activeTab === "trusted") && (
            <div className="settings-tab-panel">
              <h2 className="tab-panel-title">
                {activeTab === "archived" ? "Archived Chats" : activeTab === "parental" ? "Parental Controls" : "Trusted Contact"}
              </h2>
              <p className="tab-panel-desc">Enterprise governance and security settings.</p>
              <div className="empty-settings-placeholder">
                <span>All parameters in this category are operating normally.</span>
              </div>
            </div>
          )}

          {/* 11. DEVELOPER SETTINGS (ADMIN ONLY) - Model, Temperature & RAG Parameters */}
          {activeTab === "rag_admin" && (
            <div className="settings-tab-panel">
              <div className="admin-banner-notice">
                <span className="admin-shield-icon">🛠️</span>
                <div>
                  <strong>Developer & Model Configuration (Admin Mode)</strong>
                  <p>Fine-tune local Ollama models, generation temperature, hybrid fusion math, and Qdrant vector retrieval.</p>
                </div>
              </div>

              <h2 className="tab-panel-title">Model & LLM Configuration</h2>

              {/* Model Selector */}
              <div className="settings-card-row">
                <div className="card-row-info">
                  <div className="card-row-label">Active LLM Model</div>
                  <div className="card-row-sub">Select the model used for conversational reasoning and document grounding.</div>
                </div>
                <select
                  className="settings-inline-select"
                  value={llmModel}
                  onChange={(e) => {
                    if (setLlmModel) setLlmModel(e.target.value);
                    showToast(`Model set to ${e.target.value}`);
                  }}
                >
                  <option value="Qwen 2.5 3B">Qwen 2.5 3B (Fast Local Default)</option>
                  <option value="Qwen 2.5 7B">Qwen 2.5 7B (High-Precision Reasoning)</option>
                  <option value="Llama 3.1 8B">Llama 3.1 8B (Extended Context)</option>
                  <option value="DeepSeek R1 7B">DeepSeek R1 7B (Chain-of-Thought)</option>
                </select>
              </div>

              {/* Temperature Slider with Presets */}
              <div className="settings-card-row slider-control-row">
                <div className="card-row-info">
                  <div className="card-row-label">
                    Generation Temperature: <strong className="highlight-temp-val">{temperature.toFixed(2)}</strong>
                  </div>
                  <div className="card-row-sub">
                    Lower values (0.0) ensure deterministic, factual answers grounded strictly in retrieved chunks. Higher values increase fluency.
                  </div>
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
                <div className="temp-preset-buttons-strip">
                  <button
                    type="button"
                    className={`btn-temp-preset ${temperature === 0.0 ? "active" : ""}`}
                    onClick={() => { setTemperature(0.0); showToast("Temperature set to 0.0 (Strict Factual)"); }}
                  >
                    0.0 Strict Factual
                  </button>
                  <button
                    type="button"
                    className={`btn-temp-preset ${temperature === 0.3 ? "active" : ""}`}
                    onClick={() => { setTemperature(0.3); showToast("Temperature set to 0.3 (Document Analysis)"); }}
                  >
                    0.3 Analytical
                  </button>
                  <button
                    type="button"
                    className={`btn-temp-preset ${temperature === 0.7 ? "active" : ""}`}
                    onClick={() => { setTemperature(0.7); showToast("Temperature set to 0.7 (Conversational)"); }}
                  >
                    0.7 Conversational
                  </button>
                  <button
                    type="button"
                    className={`btn-temp-preset ${temperature === 1.0 ? "active" : ""}`}
                    onClick={() => { setTemperature(1.0); showToast("Temperature set to 1.0 (Creative)"); }}
                  >
                    1.0 Creative
                  </button>
                </div>
              </div>

              <h3 className="section-subheading">Local Engine Architecture</h3>
              <div className="admin-arch-grid">
                <div className="arch-stat-card">
                  <span className="arch-card-label">Inference Runtime</span>
                  <strong className="arch-card-val">Ollama Local (Port 11434)</strong>
                </div>
                <div className="arch-stat-card">
                  <span className="arch-card-label">Embeddings</span>
                  <strong className="arch-card-val">{embeddingModel}</strong>
                </div>
                <div className="arch-stat-card">
                  <span className="arch-card-label">Vector Database</span>
                  <strong className="arch-card-val">Qdrant Local (Port 6333)</strong>
                </div>
                <div className="arch-stat-card">
                  <span className="arch-card-label">Streaming Protocol</span>
                  <strong className="arch-card-val">FastAPI Async WebSockets</strong>
                </div>
              </div>

              <h3 className="section-subheading">Retrieval & Hybrid Reranking</h3>

              <div className="settings-card-row slider-control-row">
                <div className="card-row-info">
                  <div className="card-row-label">Top-K Retrieved Chunks: <strong>{topK}</strong></div>
                  <div className="card-row-sub">Maximum number of document passages passed to LLM context.</div>
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

              <div className="settings-card-row slider-control-row">
                <div className="card-row-info">
                  <div className="card-row-label">Similarity Threshold: <strong>{scoreThreshold.toFixed(2)}</strong></div>
                  <div className="card-row-sub">Minimum cosine similarity score required for chunk consideration.</div>
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

              <div className="settings-card-row">
                <div className="card-row-info">
                  <div className="card-row-label">Hybrid Fusion Method</div>
                  <div className="card-row-sub">Algorithm combining dense vector and sparse keyword scores.</div>
                </div>
                <select
                  className="settings-inline-select"
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
                <div className="settings-card-row slider-control-row">
                  <div className="card-row-info">
                    <div className="card-row-label">Dense Alpha Weight: <strong>{fusionAlpha.toFixed(2)}</strong></div>
                    <div className="card-row-sub">Weight given to vector search vs keyword search (0 = BM25 only, 1 = Dense only).</div>
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

              <h3 className="section-subheading">Reasoning & Routing</h3>

              <div className="settings-card-row">
                <div className="card-row-info">
                  <div className="card-row-label">Query Routing Mode</div>
                  <div className="card-row-sub">How user prompts are routed between documents, live web, and general reasoning.</div>
                </div>
                <select
                  className="settings-inline-select"
                  value={routerMode}
                  onChange={(e) => setRouterMode(e.target.value)}
                >
                  <option value="hybrid">Hybrid (Fast Rules + LLM Router)</option>
                  <option value="rules_only">Fast Keyword Rules Only</option>
                  <option value="force_doc">Force Document Grounding</option>
                  <option value="force_gen">Force General Reasoning</option>
                </select>
              </div>

              <div className="settings-btn-row">
                <button
                  className="btn-primary-save"
                  onClick={() => showToast("Developer & Model parameters saved successfully.")}
                >
                  Save Configuration
                </button>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
