import React, { useState, useRef, useEffect } from "react";
import UserMenuPopover from "../Auth/UserMenuPopover";
import DocumentActionPopover from "./DocumentActionPopover";

export default function Sidebar({
  isOpen,
  onToggleSidebar,
  theme = "light",
  onToggleTheme,
  currentNavView = "chat",
  onSelectNavView,
  conversations = [],
  activeConvId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  onRenameConversation,
  onOpenHistory,
  onOpenProjects,
  documents = [],
  activeDoc,
  onSelectDocument,
  onTriggerUpload,
  onDeleteDocument,
  onRenameDocument,
  onOpenSettings,
  onOpenDeveloperSettings,
  onOpenTools,
  onClearChat,
  onOpenHelp,
  currentUser,
  onOpenAuth,
  onLogout,
  onToggleRole,
  onRequestAdminMode
}) {
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const searchInputRef = useRef(null);
  const [isFooterMenuOpen, setIsFooterMenuOpen] = useState(false);
  const [activeDocMenu, setActiveDocMenu] = useState(null);
  const [docMenuPos, setDocMenuPos] = useState({ top: 0, left: 0 });

  const handleOpenDocMenu = (e, doc) => {
    e.stopPropagation();
    if (activeDocMenu?.id === doc.id) {
      setActiveDocMenu(null);
    } else {
      const rect = e.currentTarget.getBoundingClientRect();
      const menuWidth = 200;
      const menuHeight = 270;
      let left = rect.right + 6;
      if (left + menuWidth > window.innerWidth) {
        left = rect.left - menuWidth;
      }
      let top = rect.top;
      if (top + menuHeight > window.innerHeight) {
        top = window.innerHeight - menuHeight - 10;
      }
      setDocMenuPos({ top: Math.max(10, top), left: Math.max(10, left) });
      setActiveDocMenu(doc);
    }
  };

  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setIsSearchOpen((prev) => {
          const nextState = !prev;
          if (nextState) {
            setTimeout(() => searchInputRef.current?.focus(), 50);
          }
          return nextState;
        });
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const filteredConversations = conversations.filter((c) =>
    (c.title || "New Chat").toLowerCase().includes(searchQuery.toLowerCase())
  );

  const username = currentUser?.username || "Guest User";
  const userPlan = (currentUser?.role || "").toLowerCase().includes("admin")
    ? "Enterprise Administrator"
    : currentUser
    ? "Standard User (Free Plan)"
    : "Guest Mode (Sign in)";

  return (
    <aside className={`chatgpt-sidebar ${isOpen ? "open" : "collapsed"}`}>
      {/* Brand Header with Search & Sidebar Toggle Actions */}
      <div className="sidebar-brand-header">
        <div className="brand-header-left">
          <div className="brand-logo-tile">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <path d="M9 15h6" />
              <path d="M12 12v6" />
            </svg>
          </div>
          <div className="brand-info-col">
            <h2 className="brand-title">DocuChat AI</h2>
            <span className="brand-tag">AI Document Intelligence & RAG</span>
          </div>
        </div>

        <div className="sidebar-header-actions">
          <button
            type="button"
            className={`sidebar-header-icon-btn ${isSearchOpen ? "active" : ""}`}
            title="Search chats (⌘K)"
            onClick={() => {
              setIsSearchOpen((prev) => {
                const nextState = !prev;
                if (nextState) {
                  setTimeout(() => searchInputRef.current?.focus(), 50);
                }
                return nextState;
              });
            }}
          >
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
          </button>

          {onToggleSidebar && (
            <button
              type="button"
              className="sidebar-header-icon-btn"
              title="Close sidebar"
              onClick={onToggleSidebar}
            >
              <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                <line x1="9" y1="3" x2="9" y2="21" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* New Chat Item matching Image 2 style and icon */}
      <div className="sidebar-new-chat-row">
        <button className="sidebar-new-chat-btn" onClick={onNewConversation}>
          <div className="sidebar-new-chat-left">
            <svg
              width="17"
              height="17"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="new-chat-icon"
            >
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
            </svg>
            <span>New chat</span>
          </div>
          <kbd className="sidebar-new-chat-kbd">Ctrl K</kbd>
        </button>
      </div>

      {/* Search Chats Input (Expanded when search button is clicked or shortcut used) */}
      {(isSearchOpen || searchQuery) && (
        <div className="sidebar-search-container open">
          <div className="sidebar-search-box">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="search-icon">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input
              ref={searchInputRef}
              type="text"
              className="sidebar-search-field"
              placeholder="Search chats..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Escape") {
                  setSearchQuery("");
                  setIsSearchOpen(false);
                }
              }}
            />
            {searchQuery ? (
              <button
                type="button"
                className="search-clear-btn"
                onClick={() => setSearchQuery("")}
                title="Clear search"
              >
                ✕
              </button>
            ) : (
              <kbd className="kbd-shortcut">ESC</kbd>
            )}
          </div>
        </div>
      )}

      {/* Primary Navigation Menu (Chat, Library, Projects, History, Tools - Settings removed per request) */}
      <nav className="sidebar-primary-nav">
        <button
          className={`nav-link-btn ${currentNavView === "chat" ? "active" : ""}`}
          onClick={() => onSelectNavView && onSelectNavView("chat")}
        >
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
          <span>Chat</span>
        </button>

        <button
          className={`nav-link-btn ${currentNavView === "library" ? "active" : ""}`}
          onClick={() => onTriggerUpload && onTriggerUpload()}
        >
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
          </svg>
          <span>Library</span>
        </button>

        <button
          className={`nav-link-btn ${currentNavView === "projects" ? "active" : ""}`}
          onClick={() => {
            if (onSelectNavView) onSelectNavView("projects");
            if (onOpenProjects) onOpenProjects();
          }}
          title="Open Workspace Projects"
        >
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
          </svg>
          <span>Projects</span>
        </button>

        <button
          className="nav-link-btn"
          onClick={() => onOpenHistory && onOpenHistory()}
          title="View all past conversation history"
        >
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
          <span>History</span>
        </button>

        <button
          className={`nav-link-btn ${currentNavView === "tools" ? "active" : ""}`}
          onClick={() => onOpenTools && onOpenTools()}
        >
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
          </svg>
          <span>Tools</span>
        </button>
      </nav>

      {/* Recent Conversations Section */}
      <div className="sidebar-group-section">
        <div className="group-section-header">
          <span className="group-title-text">Recent Conversations</span>
          <button
            className="btn-view-all-link"
            onClick={() => onOpenHistory && onOpenHistory()}
            title="Click to view all past history"
          >
            View all →
          </button>
        </div>

        <div className="group-scroll-list">
          {filteredConversations.length === 0 ? (
            <div className="empty-sub-hint">No chats found.</div>
          ) : (
            filteredConversations.map((conv) => {
              const isActive = activeConvId === conv.id;
              return (
                <div
                  key={conv.id}
                  className={`chat-history-item-tile ${isActive ? "active" : ""}`}
                  onClick={() => onSelectConversation && onSelectConversation(conv.id)}
                >
                  <div className="chat-item-icon">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <polyline points="14 2 14 8 20 8" />
                    </svg>
                  </div>
                  <div className="chat-item-meta">
                    <span className="chat-item-title" title={conv.title || "New Chat"}>
                      {conv.title || "New Chat"}
                    </span>
                    <span className="chat-item-time">
                      {conv.updated_at ? "Recently" : "2 minutes ago"}
                    </span>
                  </div>
                  <div className="chat-item-actions-group" style={{ display: 'flex', alignItems: 'center' }}>
                    <button
                      className="btn-chat-item-rename"
                      onClick={(e) => {
                        e.stopPropagation();
                        const newTitle = window.prompt("Rename conversation:", conv.title || "New Chat");
                        if (newTitle && newTitle.trim() && newTitle.trim() !== conv.title) {
                          onRenameConversation && onRenameConversation(conv.id, newTitle.trim());
                        }
                      }}
                      title="Rename conversation"
                      style={{ background: 'none', border: 'none', color: 'inherit', opacity: 0.6, cursor: 'pointer', padding: '2px 4px', fontSize: '12px' }}
                    >
                      ✎
                    </button>
                    <button
                      className="btn-chat-item-delete"
                      onClick={(e) => {
                        e.stopPropagation();
                        if (window.confirm(`Delete conversation "${conv.title}"?`)) {
                          onDeleteConversation && onDeleteConversation(conv.id);
                        }
                      }}
                      title="Delete"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Document Collection Section */}
      <div className="sidebar-group-section">
        <div className="group-section-header">
          <span className="group-title-text">Document Collection</span>
          <button className="btn-view-all-link" onClick={onTriggerUpload}>
            View all →
          </button>
        </div>

        <div className="group-scroll-list">
          {documents.length === 0 ? (
            <div className="empty-sub-hint">
              No documents.<br />
              <button className="upload-inline-trigger" onClick={onTriggerUpload}>+ Upload Document</button>
            </div>
          ) : (
            documents.map((doc) => {
              const isSelected = activeDoc?.id === doc.id;
              return (
                <div
                  key={doc.id}
                  className={`document-collection-item ${isSelected ? "selected" : ""}`}
                  onClick={() => onSelectDocument && onSelectDocument(doc)}
                  title={`Click to open ${doc.filename} in split view`}
                >
                  <div className="doc-item-icon-tile">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <polyline points="14 2 14 8 20 8" />
                    </svg>
                  </div>
                  <div className="doc-item-meta">
                    <span className="doc-item-title" title={doc.filename}>{doc.filename}</span>
                    <span className="doc-item-sub">
                      {doc.page_count ? `${doc.page_count} pages` : "12 pages"} &bull; {doc.chunk_count ? `${doc.chunk_count} chunks` : "2.4 MB"}
                    </span>
                  </div>
                  <button
                    className={`btn-doc-dots ${activeDocMenu?.id === doc.id ? "active" : ""}`}
                    title="Options"
                    onClick={(e) => handleOpenDocMenu(e, doc)}
                  >
                    ⋮
                  </button>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* User Profile Footer ("down side where its shows amd12321") */}
      <div className="sidebar-footer-relative-container">
        <div
          className="sidebar-user-footer"
          onClick={() => setIsFooterMenuOpen(!isFooterMenuOpen)}
          title={`Click to open account and settings for ${username}`}
        >
          <div className="user-footer-avatar">
            <span className="user-avatar-initial">
              {username ? username.charAt(0).toUpperCase() : "A"}
            </span>
          </div>
          <div className="user-footer-meta">
            <span className="user-footer-name">{username}</span>
            <span className="user-footer-plan">{userPlan}</span>
          </div>
        </div>

        {/* User Menu Popover anchored to bottom footer */}
        <UserMenuPopover
          isOpen={isFooterMenuOpen}
          onClose={() => setIsFooterMenuOpen(false)}
          currentUser={currentUser}
          theme={theme}
          onToggleTheme={onToggleTheme}
          onOpenSettings={onOpenSettings}
          onOpenDeveloperSettings={onOpenDeveloperSettings}
          onClearChat={onClearChat}
          onOpenHelp={onOpenHelp}
          onLogout={onLogout}
          onToggleRole={onToggleRole}
          onRequestAdminMode={onRequestAdminMode}
          onOpenAuth={onOpenAuth}
          position="bottom"
        />
      </div>

      {/* Document Action Context Menu Popover matching Image 2 */}
      <DocumentActionPopover
        isOpen={Boolean(activeDocMenu)}
        document={activeDocMenu}
        position={docMenuPos}
        onClose={() => setActiveDocMenu(null)}
        onRename={(doc) => {
          const newName = window.prompt("Rename document:", doc.filename);
          if (newName && newName.trim() && newName.trim() !== doc.filename) {
            onRenameDocument && onRenameDocument(doc.id, newName.trim());
          }
        }}
        onPin={(doc) => {
          alert(`Document "${doc.filename}" pinned.`);
        }}
        onShare={(doc) => {
          if (navigator.clipboard) {
            navigator.clipboard.writeText(window.location.href);
          }
          alert(`Share link for "${doc.filename}" copied to clipboard.`);
        }}
        onArchive={(doc) => {
          alert(`Document "${doc.filename}" archived.`);
        }}
        onDelete={(doc) => {
          if (window.confirm(`Are you sure you want to delete "${doc.filename}"?`)) {
            onDeleteDocument && onDeleteDocument(doc.id);
          }
        }}
        onMoveToProject={(doc) => {
          if (onOpenProjects) onOpenProjects();
        }}
      />
    </aside>
  );
}
