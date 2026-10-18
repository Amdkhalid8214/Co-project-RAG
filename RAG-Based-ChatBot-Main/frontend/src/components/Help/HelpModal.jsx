import React from "react";

export default function HelpModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="help-modal-backdrop" onClick={onClose}>
      <div className="help-modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="help-modal-header">
          <div className="help-header-title">
            <div className="help-icon-tile">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
            </div>
            <div>
              <h3>DocuChat AI Help & Guide</h3>
              <p>Everything you need to know about using DocuChat AI</p>
            </div>
          </div>
          <button className="btn-close-help" onClick={onClose}>✕</button>
        </div>

        <div className="help-modal-body">
          {/* Quick Guide Grid */}
          <div className="help-features-grid">
            <div className="help-feature-card">
              <div className="help-card-icon">📄</div>
              <h4>Document Grounding</h4>
              <p>Upload documents via the Library or composer clip. Click any citation chip (e.g. <code>[1]</code>) to immediately jump to the highlighted evidence bounding box in the side viewer.</p>
            </div>

            <div className="help-feature-card">
              <div className="help-card-icon">🌐</div>
              <h4>Live Web Search</h4>
              <p>Toggle the <strong>Web</strong> button on the right of the search input to supplement document answers with live real-time internet data.</p>
            </div>

            <div className="help-feature-card">
              <div className="help-card-icon">🛡️</div>
              <h4>Admin Mode</h4>
              <p>Click the <strong>User Mode / Admin Mode</strong> button at the top (protected by your password: <code>amd12321</code>) to tune models, temperature presets, and RAG thresholds.</p>
            </div>

            <div className="help-feature-card">
              <div className="help-card-icon">📁</div>
              <h4>Workspace Projects</h4>
              <p>Organize related files and research into dedicated project workspaces using the <strong>Projects</strong> sidebar option.</p>
            </div>
          </div>

          {/* Keyboard Shortcuts Section */}
          <div className="help-shortcuts-section">
            <h4>Keyboard Shortcuts</h4>
            <div className="shortcuts-table">
              <div className="shortcut-row">
                <span className="shortcut-label">Search conversations</span>
                <kbd className="kbd-badge">⌘ K / Ctrl + K</kbd>
              </div>
              <div className="shortcut-row">
                <span className="shortcut-label">Send chat message</span>
                <kbd className="kbd-badge">Enter</kbd>
              </div>
              <div className="shortcut-row">
                <span className="shortcut-label">Insert new line</span>
                <kbd className="kbd-badge">Shift + Enter</kbd>
              </div>
              <div className="shortcut-row">
                <span className="shortcut-label">Close modal or popover</span>
                <kbd className="kbd-badge">Esc</kbd>
              </div>
            </div>
          </div>
        </div>

        <div className="help-modal-footer">
          <span className="help-footer-status">● System Status: Online & Operational</span>
          <button className="btn-done-help" onClick={onClose}>Got it</button>
        </div>
      </div>
    </div>
  );
}
