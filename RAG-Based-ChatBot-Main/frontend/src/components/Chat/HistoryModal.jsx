import React, { useState } from "react";

export default function HistoryModal({
  isOpen,
  onClose,
  conversations = [],
  activeConvId,
  onSelectConversation,
  onDeleteConversation,
  onNewConversation,
  onClearAllConversations
}) {
  const [search, setSearch] = useState("");

  if (!isOpen) return null;

  const filtered = conversations.filter((c) =>
    (c.title || "Untitled Conversation").toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="history-modal-backdrop" onClick={onClose}>
      <div className="history-modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="history-modal-header">
          <div className="history-header-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
            <h3>Conversation History</h3>
            <span className="history-count-badge">{conversations.length} total</span>
          </div>

          <div className="history-header-actions">
            <button
              className="btn-history-new-chat"
              onClick={() => {
                onNewConversation();
                onClose();
              }}
            >
              + New Chat
            </button>
            <button className="btn-close-history" onClick={onClose} title="Close">
              ✕
            </button>
          </div>
        </div>

        {/* Search Input */}
        <div className="history-search-bar">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="text"
            placeholder="Search past conversations..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            autoFocus
          />
          {search && (
            <button className="btn-clear-search" onClick={() => setSearch("")}>
              ✕
            </button>
          )}
        </div>

        {/* Conversation List */}
        <div className="history-items-scroll">
          {filtered.length === 0 ? (
            <div className="history-empty-state">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
              <p>No conversations found matching "{search}"</p>
            </div>
          ) : (
            filtered.map((conv) => {
              const isActive = activeConvId === conv.id;
              return (
                <div
                  key={conv.id}
                  className={`history-card-item ${isActive ? "active" : ""}`}
                  onClick={() => {
                    onSelectConversation(conv.id);
                    onClose();
                  }}
                >
                  <div className="history-item-left">
                    <div className="history-icon-bubble">
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                      </svg>
                    </div>
                    <div className="history-meta">
                      <strong className="history-title" title={conv.title}>
                        {conv.title || "Untitled Conversation"}
                      </strong>
                      <span className="history-timestamp">
                        {conv.updated_at ? new Date(conv.updated_at).toLocaleString() : "Recently active"}
                      </span>
                    </div>
                  </div>

                  <div className="history-item-actions">
                    <button
                      className="btn-history-delete"
                      onClick={(e) => {
                        e.stopPropagation();
                        if (window.confirm(`Delete conversation "${conv.title}"?`)) {
                          onDeleteConversation(conv.id);
                        }
                      }}
                      title="Delete conversation"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="3 6 5 6 21 6" />
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                      </svg>
                    </button>
                    <span className="history-arrow">›</span>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="history-modal-footer">
          <button
            className="btn-history-clear-all"
            onClick={() => {
              if (window.confirm("Are you sure you want to delete all conversation history?")) {
                onClearAllConversations();
                onClose();
              }
            }}
          >
            Clear All History
          </button>
          <span className="history-footer-hint">Click any conversation to load its message thread.</span>
        </div>
      </div>
    </div>
  );
}
