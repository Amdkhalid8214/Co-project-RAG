import React, { useEffect, useRef } from "react";

export default function UserMenuPopover({
  isOpen,
  onClose,
  currentUser,
  theme = "light",
  onToggleTheme,
  onOpenSettings,
  onOpenDeveloperSettings,
  onClearChat,
  onOpenHelp,
  onLogout,
  onToggleRole,
  onRequestAdminMode,
  onOpenAuth,
  position = "bottom"
}) {
  const popoverRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (
        popoverRef.current &&
        !popoverRef.current.contains(e.target) &&
        !e.target.closest(".sidebar-user-footer")
      ) {
        onClose();
      }
    };
    const handleEsc = (e) => {
      if (e.key === "Escape") onClose();
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      document.addEventListener("keydown", handleEsc);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEsc);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const username = currentUser?.username || "Guest User";
  const role = currentUser?.role || "Free Plan";
  const isAdmin = role.toLowerCase().includes("admin");

  return (
    <div className={`user-menu-popover position-${position}`} ref={popoverRef}>
      {/* User Header */}
      <div className="user-menu-header">
        <div className="user-menu-avatar">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
        </div>
        <div className="user-menu-info">
          <div className="user-menu-name">{username}</div>
          <div className="user-menu-role-badge">
            <span className={`role-dot ${isAdmin ? "admin" : "user"}`}></span>
            <span>{isAdmin ? "Enterprise Administrator" : "Standard User (Free Plan)"}</span>
          </div>
        </div>
      </div>

      <div className="user-menu-divider"></div>

      {/* Role Toggle Switcher (Password protected when upgrading to Admin Mode) */}
      <div className="user-menu-section">
        <button
          className="user-menu-item-btn role-switch-btn"
          onClick={() => {
            if (!isAdmin) {
              if (onRequestAdminMode) onRequestAdminMode();
              else onToggleRole();
            } else {
              onToggleRole();
            }
            onClose();
          }}
          title={isAdmin ? "Switch to standard User Mode" : "Switch to Admin Mode (Password protected)"}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
            <circle cx="8.5" cy="7.5" r="4" />
            <polyline points="17 11 19 13 23 9" />
          </svg>
          <div className="role-switch-text">
            <span>{isAdmin ? "Switch to User Mode" : "Switch to Admin Mode"}</span>
            <small>{isAdmin ? "Return to standard user experience" : "Password protected: unlock Developer Settings"}</small>
          </div>
        </button>
      </div>

      <div className="user-menu-divider"></div>

      {/* Main Options: Settings, Clear Chat, Help, Switch Account */}
      <div className="user-menu-section">
        {/* Settings Option */}
        <button
          className="user-menu-item-btn"
          onClick={() => {
            if (onOpenSettings) onOpenSettings();
            onClose();
          }}
          title="Open application appearance and system preferences"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
          <span>Settings</span>
        </button>

        {/* Quick Theme Switcher */}
        {onToggleTheme && (
          <button
            type="button"
            className="user-menu-item-btn"
            onClick={() => {
              onToggleTheme();
              onClose();
            }}
            title={`Switch to ${theme === "dark" ? "Light" : "Dark"} Mode`}
          >
            {theme === "dark" ? (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="5" />
                <line x1="12" y1="1" x2="12" y2="3" />
                <line x1="12" y1="21" x2="12" y2="23" />
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                <line x1="1" y1="2" x2="3" y2="12" />
                <line x1="21" y1="12" x2="23" y2="12" />
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
              </svg>
            ) : (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
              </svg>
            )}
            <span>{theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode"}</span>
          </button>
        )}

        {/* Clear Current Chat Option */}
        {onClearChat && (
          <button
            className="user-menu-item-btn clear-chat-menu-btn"
            onClick={() => {
              onClearChat();
              onClose();
            }}
            title="Clear all messages in active conversation"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="3 6 5 6 21 6" />
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
            </svg>
            <span>Clear Current Chat</span>
          </button>
        )}

        {/* Help Option */}
        <button
          className="user-menu-item-btn"
          onClick={() => {
            if (onOpenHelp) onOpenHelp();
            onClose();
          }}
          title="View help guide, tips, and keyboard shortcuts"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
          <span>Help & Guide</span>
        </button>

        {/* Switch Account Option */}
        <button
          className="user-menu-item-btn"
          onClick={() => {
            if (onOpenAuth) onOpenAuth();
            onClose();
          }}
          title="Log into another account or switch tenant"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
            <circle cx="8.5" cy="7.5" r="4" />
          </svg>
          <span>Switch Account</span>
        </button>
      </div>

      <div className="user-menu-divider"></div>

      {/* Logout button */}
      <div className="user-menu-section">
        <button
          className="user-menu-item-btn logout-btn"
          onClick={() => {
            onLogout();
            onClose();
          }}
          title="Log out of DocuChat AI"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
            <polyline points="16 17 21 12 16 7" />
            <line x1="21" y1="12" x2="9" y2="12" />
          </svg>
          <span>Log out</span>
        </button>
      </div>
    </div>
  );
}
