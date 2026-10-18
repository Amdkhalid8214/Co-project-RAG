import React, { useState } from "react";

export default function AdminPasswordModal({ isOpen, onClose, onSuccess }) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [showPwd, setShowPwd] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    const storedPwd = localStorage.getItem("docuchat_admin_pwd") || "amd12321";
    // Allow configured password, username password, or standard admin fallback
    const valid =
      password.trim() === storedPwd ||
      password.trim() === "amd12321" ||
      password.trim() === "admin123" ||
      password.trim() === "admin";

    if (valid) {
      setError("");
      setPassword("");
      onSuccess();
      onClose();
    } else {
      setError("Incorrect administrator password. Access denied.");
    }
  };

  const handleClose = () => {
    setError("");
    setPassword("");
    onClose();
  };

  return (
    <div className="admin-pwd-modal-backdrop" onClick={handleClose}>
      <div className="admin-pwd-modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="admin-pwd-modal-header">
          <div className="admin-pwd-icon-tile">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
          </div>
          <div className="admin-pwd-header-text">
            <h3>Administrator Authentication</h3>
            <p>Enter your password to unlock Developer Settings and model tuning</p>
          </div>
          <button className="btn-close-admin-pwd" onClick={handleClose}>
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="admin-pwd-form">
          {error && <div className="admin-pwd-error-alert">{error}</div>}

          <div className="admin-pwd-input-group">
            <label>Admin Password</label>
            <div className="admin-pwd-input-wrapper">
              <input
                type={showPwd ? "text" : "password"}
                placeholder="Enter admin password..."
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (error) setError("");
                }}
                autoFocus
                required
              />
              <button
                type="button"
                className="btn-toggle-pwd-vis"
                onClick={() => setShowPwd(!showPwd)}
                title={showPwd ? "Hide password" : "Show password"}
              >
                {showPwd ? "🙈" : "👁️"}
              </button>
            </div>
            <span className="admin-pwd-hint">Protected mode: only authorized administrators can access.</span>
          </div>

          <div className="admin-pwd-actions">
            <button type="button" className="btn-cancel-admin-pwd" onClick={handleClose}>
              Cancel
            </button>
            <button type="submit" className="btn-submit-admin-pwd">
              Unlock Admin Mode
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
