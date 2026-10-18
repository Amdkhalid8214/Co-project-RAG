import React, { useRef, useEffect } from "react";
import MarkdownRenderer from "./MarkdownRenderer";

export default function ChatArea({
  messages = [],
  isGenerating,
  onCitationClick,
  onQuickPromptClick,
  activeDoc
}) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isGenerating]);

  const hasMessages = messages && messages.length > 0;

  return (
    <div className="chatgpt-chat-area-container">
      <div className="chatgpt-messages-scroll-stage">
        {!hasMessages ? (
          <div className="chatgpt-empty-conversation-state">
            {/* Completely cleared empty chat state */}
          </div>
        ) : (
          <div className="chatgpt-conversation-stream">
            {messages.map((msg, idx) => {
              const isUser = msg.role === "user";
              const msgId = msg.id || idx;

              if (isUser) {
                return (
                  <div key={msgId} className="chat-msg-row user-row">
                    <div className="user-bubble-box">
                      <p className="msg-text">{msg.content}</p>
                      <div className="user-time-row">
                        <span className="msg-time">
                          {msg.created_at
                            ? new Date(msg.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
                            : "Just now"}
                        </span>
                        <span className="msg-check">✓</span>
                      </div>
                    </div>
                    <div className="user-avatar-outline">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                        <circle cx="12" cy="7" r="4" />
                      </svg>
                    </div>
                  </div>
                );
              }

              // Filter out completely empty assistant messages if generation ended
              if (!msg.content && !isGenerating && (!msg.citations || msg.citations.length === 0)) {
                return null;
              }

              return (
                <div key={msgId} className="chat-msg-row asst-row">
                  {/* Modern AI Bot Avatar (replacing padlock) */}
                  <div className="asst-bot-avatar" title="DocuChat AI">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M12 2a2 2 0 0 1 2 2v2h4a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4V4a2 2 0 0 1 2-2z" />
                      <circle cx="9" cy="13" r="1.5" fill="currentColor" />
                      <circle cx="15" cy="13" r="1.5" fill="currentColor" />
                      <path d="M10 17h4" />
                    </svg>
                  </div>

                  <div className="asst-bubble-wrapper">
                    {msg.router_badge && (
                      <div className="asst-router-badge-pill">
                        <span>{msg.router_badge}</span>
                      </div>
                    )}

                    <div className="asst-markdown-text">
                      {msg.content ? (
                        <MarkdownRenderer
                          content={msg.content}
                          citations={msg.citations}
                          onCitationClick={onCitationClick}
                        />
                      ) : (
                        <div className="typing-dots-indicator">
                          <span></span>
                          <span></span>
                          <span></span>
                        </div>
                      )}
                    </div>

                    <div className="asst-footer-time">
                      {msg.created_at
                        ? new Date(msg.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
                        : "Just now"}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
