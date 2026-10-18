import React, { useEffect, useRef } from "react";

export default function DocumentActionPopover({
  isOpen,
  onClose,
  document: doc,
  position = { top: 0, left: 0 },
  onRename,
  onPin,
  onShare,
  onArchive,
  onDelete,
  onMoveToProject,
}) {
  const popoverRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (
        popoverRef.current &&
        !popoverRef.current.contains(e.target) &&
        !e.target.closest(".btn-doc-dots")
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

  if (!isOpen || !doc) return null;

  return (
    <div
      className="doc-actions-menu-popover"
      ref={popoverRef}
      style={{
        position: "fixed",
        top: `${position.top}px`,
        left: `${position.left}px`,
        zIndex: 9999,
      }}
      onClick={(e) => e.stopPropagation()}
    >
      {/* 1. Rename */}
      <button
        type="button"
        className="doc-menu-item"
        onClick={() => {
          onRename && onRename(doc);
          onClose();
        }}
      >
        <svg
          width="15"
          height="15"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="doc-menu-item-icon"
        >
          <path d="M12 20h9" />
          <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
        </svg>
        <span>Rename</span>
      </button>

      {/* 2. Pin */}
      <button
        type="button"
        className="doc-menu-item"
        onClick={() => {
          onPin && onPin(doc);
          onClose();
        }}
      >
        <svg
          width="15"
          height="15"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="doc-menu-item-icon"
        >
          <line x1="12" y1="17" x2="12" y2="22" />
          <path d="M5 17h14v-1.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V6a3 3 0 0 0-6 0v4.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24Z" />
        </svg>
        <span>Pin</span>
      </button>

      {/* Divider */}
      <div className="doc-menu-divider" />

      {/* 3. Share */}
      <button
        type="button"
        className="doc-menu-item"
        onClick={() => {
          onShare && onShare(doc);
          onClose();
        }}
      >
        <svg
          width="15"
          height="15"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="doc-menu-item-icon"
        >
          <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" />
          <polyline points="16 6 12 2 8 6" />
          <line x1="12" y1="2" x2="12" y2="15" />
        </svg>
        <span>Share</span>
      </button>

      {/* Divider */}
      <div className="doc-menu-divider" />

      {/* 4. Archive */}
      <button
        type="button"
        className="doc-menu-item"
        onClick={() => {
          onArchive && onArchive(doc);
          onClose();
        }}
      >
        <svg
          width="15"
          height="15"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="doc-menu-item-icon"
        >
          <polyline points="21 8 21 21 3 21 3 8" />
          <rect x="1" y="3" width="22" height="5" />
          <line x1="10" y1="12" x2="14" y2="12" />
        </svg>
        <span>Archive</span>
      </button>

      {/* 5. Delete (Red) */}
      <button
        type="button"
        className="doc-menu-item danger"
        onClick={() => {
          onDelete && onDelete(doc);
          onClose();
        }}
      >
        <svg
          width="15"
          height="15"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="doc-menu-item-icon"
        >
          <polyline points="3 6 5 6 21 6" />
          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
        </svg>
        <span>Delete</span>
      </button>

      {/* Divider */}
      <div className="doc-menu-divider" />

      {/* 6. Move to project > */}
      <button
        type="button"
        className="doc-menu-item space-between"
        onClick={() => {
          onMoveToProject && onMoveToProject(doc);
          onClose();
        }}
      >
        <div className="doc-menu-item-left">
          <svg
            width="15"
            height="15"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="doc-menu-item-icon"
          >
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
          </svg>
          <span>Move to project</span>
        </div>
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="chevron-icon"
        >
          <polyline points="9 18 15 12 9 6" />
        </svg>
      </button>
    </div>
  );
}
