import React, { useState } from "react";

export default function AuthModal({
  isOpen,
  onClose,
  onLogin,
  onRegister,
  onDemoLogin
}) {
  const [tab, setTab] = useState("login"); // "login" | "register"
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (tab === "login") {
        await onLogin(username.trim(), password);
      } else {
        await onRegister(username.trim(), password, email.trim() || null);
      }
      onClose();
    } catch (err) {
      setError(err.message || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  const handleDemo = async (role = "admin") => {
    setError("");
    setLoading(true);
    try {
      await onDemoLogin(role);
      onClose();
    } catch (err) {
      setError(err.message || "Demo login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-modal-overlay" onClick={onClose}>
      <div className="auth-modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="auth-modal-header">
          <div className="auth-title-stack">
            <h3 className="auth-main-title">
              {tab === "login" ? "Sign In to DocuChat AI" : "Create Enterprise Account"}
            </h3>
            <p className="auth-subtitle">
              {tab === "login"
                ? "Enter your credentials to access your document workspaces"
                : "Register for an enterprise document intelligence account"}
            </p>
          </div>
          <button className="auth-close-btn" onClick={onClose} title="Close">
            ✕
          </button>
        </div>

        <div className="auth-tab-buttons">
          <button
            type="button"
            className={`auth-tab-pill ${tab === "login" ? "active" : ""}`}
            onClick={() => {
              setTab("login");
              setError("");
            }}
          >
            Log In
          </button>
          <button
            type="button"
            className={`auth-tab-pill ${tab === "register" ? "active" : ""}`}
            onClick={() => {
              setTab("register");
              setError("");
            }}
          >
            Register
          </button>
        </div>

        {error && <div className="auth-error-banner">{error}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label className="form-label">Username</label>
            <input
              type="text"
              required
              className="auth-input-field"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. admin or your username"
            />
          </div>

          {tab === "register" && (
            <div className="form-group">
              <label className="form-label">Email (Optional)</label>
              <input
                type="email"
                className="auth-input-field"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@company.ai"
              />
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              type="password"
              required
              className="auth-input-field"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </div>

          <button type="submit" className="btn-auth-submit" disabled={loading}>
            {loading ? "Processing..." : tab === "login" ? "Sign In" : "Register"}
          </button>
        </form>

        <div className="auth-divider">
          <span>OR QUICK ACCESS</span>
        </div>

        <div className="auth-demo-actions-col">
          <button
            type="button"
            className="btn-demo-quick-login admin-login-btn"
            onClick={() => handleDemo("admin")}
            disabled={loading}
          >
            <span className="demo-icon">🚀</span>
            <div className="demo-btn-label">
              <strong>Instant Demo Login (Admin)</strong>
              <small>Full access to RAG parameters & vector pipeline</small>
            </div>
          </button>

          <button
            type="button"
            className="btn-demo-quick-login user-login-btn"
            onClick={() => handleDemo("user")}
            disabled={loading}
          >
            <span className="demo-icon">👤</span>
            <div className="demo-btn-label">
              <strong>Instant Demo Login (User)</strong>
              <small>Standard clean interface without admin internals</small>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}
