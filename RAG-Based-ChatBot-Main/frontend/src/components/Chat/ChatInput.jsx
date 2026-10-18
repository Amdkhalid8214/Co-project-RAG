import React, { useRef, useEffect } from "react";

export default function ChatInput({
  inputMessage,
  setInputMessage,
  onSendMessage,
  isGenerating,
  onStopGenerating,
  onOpenFileUpload,
  onToggleTools,
  toolsOpen,
  disabled,
  webMode = false,
  setWebMode
}) {
  const textareaRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [inputMessage]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!isGenerating && inputMessage.trim()) {
        onSendMessage();
      }
    }
  };

  return (
    <div className="chatgpt-composer-wrapper">
      {/* Real-Web Mode Banner if active */}
      {webMode && (
        <div className="composer-mode-badge-strip">
          <span className="mode-badge-dot"></span>
          <span>🌐 Real-Web Mode Active: Responses will be grounded in live web search</span>
          <button
            className="btn-disable-web-badge"
            onClick={() => setWebMode && setWebMode(false)}
            title="Disable Web Mode"
          >
            ✕
          </button>
        </div>
      )}

      <div className="chatgpt-input-bar">
        {/* Left Controls: Plus (Tools) and Paperclip (Attach) */}
        <div className="composer-left-actions-group">
          <button
            className={`btn-composer-plus ${toolsOpen ? "active" : ""}`}
            onClick={onToggleTools}
            title="Tools & Extensions (+)"
            type="button"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
          </button>

          <button
            className="btn-composer-attach"
            title="Attach Document"
            onClick={onOpenFileUpload}
            disabled={disabled || isGenerating}
            type="button"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
            </svg>
          </button>
        </div>

        {/* Text Input Area */}
        <textarea
          ref={textareaRef}
          className="composer-textarea"
          placeholder={webMode ? "Ask anything using live web search..." : "Ask anything about your documents..."}
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          rows={1}
        />

        {/* Right Controls (Opposite Side): Real-Web Mode Toggle, Mic, Send */}
        <div className="composer-right-actions-group">
          <button
            className={`btn-composer-web-toggle ${webMode ? "active" : ""}`}
            title={webMode ? "Real-Web Mode is ON (Click to turn off)" : "Turn ON Real-Web Mode (searches live internet)"}
            onClick={() => setWebMode && setWebMode(!webMode)}
            type="button"
          >
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="2" y1="12" x2="22" y2="12" />
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
            </svg>
            <span className="web-toggle-pill-tag">Web</span>
          </button>

          <button
            className="btn-composer-mic"
            title="Voice input"
            type="button"
            onClick={() => {
              alert("Voice recognition input active. Speak into your microphone.");
            }}
          >
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
              <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
              <line x1="12" y1="19" x2="12" y2="23" />
              <line x1="8" y1="23" x2="16" y2="23" />
            </svg>
          </button>

          {isGenerating ? (
            <button
              className="btn-composer-stop"
              onClick={onStopGenerating}
              title="Stop generating"
              type="button"
            >
              <div className="stop-square"></div>
            </button>
          ) : (
            <button
              className="btn-composer-send"
              onClick={onSendMessage}
              disabled={disabled || !inputMessage.trim()}
              title="Send (Enter)"
              type="button"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="19" x2="12" y2="5" />
                <polyline points="5 12 12 5 19 12" />
              </svg>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
