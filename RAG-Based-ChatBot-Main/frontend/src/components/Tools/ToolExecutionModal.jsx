import React, { useState } from "react";

export default function ToolExecutionModal({
  isOpen,
  toolId,
  onClose,
  activeDoc,
  onInsertIntoChat,
  onExecutePrompt
}) {
  // Web search state
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState(null);
  const [isSearching, setIsSearching] = useState(false);

  if (!isOpen) return null;

  const docName = activeDoc ? activeDoc.filename : "Active Document";

  const handleTriggerAction = (promptText, executeNow = true) => {
    if (executeNow && onExecutePrompt) {
      onExecutePrompt(promptText);
    } else if (onInsertIntoChat) {
      onInsertIntoChat(promptText);
    }
    onClose();
  };

  const handleExecuteWebSearch = async () => {
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    setSearchResults(null);
    try {
      const res = await fetch("http://localhost:5000/api/tools/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tool: "web_search",
          arguments: { query: searchQuery }
        })
      });
      const data = await res.json();
      setSearchResults(data.results || "No results returned.");
    } catch (err) {
      setSearchResults(`Search service error: ${err.message}`);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="tool-modal-backdrop" onClick={onClose}>
      <div className="tool-modal-dialog" onClick={(e) => e.stopPropagation()}>
        <div className="tool-modal-header">
          <h3 className="tool-modal-title">
            {toolId === "web_search" && "🌐 Web Search"}
            {toolId === "create_document" && "📄 Create Document Report"}
          </h3>
          <button className="btn-tool-modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="tool-modal-body">
          {/* Web Search */}
          {toolId === "web_search" && (
            <div className="tool-websearch-view">
              <p className="tool-desc-text">Search live public web sources with automated citations and factual grounding.</p>
              <div className="calc-input-row">
                <input
                  type="text"
                  className="calc-math-input"
                  placeholder="e.g. Adam optimizer vs AdamW benchmarks"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleExecuteWebSearch()}
                />
                <button className="btn-calc-execute" onClick={handleExecuteWebSearch} disabled={isSearching}>
                  {isSearching ? "Searching..." : "Search"}
                </button>
              </div>
              {searchResults && (
                <div className="search-results-box">
                  <div className="search-res-text">{searchResults}</div>
                  <div style={{ display: "flex", gap: "8px", marginTop: "10px" }}>
                    <button
                      className="btn-tool-primary"
                      onClick={() => handleTriggerAction(searchQuery, true)}
                    >
                      ⚡ Ask DocuChat with Live Web
                    </button>
                    <button
                      className="btn-tool-secondary"
                      onClick={() =>
                        handleTriggerAction(`Web Search results for "${searchQuery}":\n${searchResults}`, false)
                      }
                    >
                      Insert into Input
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Create Document */}
          {toolId === "create_document" && (
            <div className="tool-doc-view">
              <p className="tool-desc-text">
                Draft a formal professional executive document report with structured headings, citations, and conclusions from{" "}
                <strong>{docName}</strong>.
              </p>
              <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginTop: "16px" }}>
                <button
                  className="btn-tool-primary full"
                  onClick={() =>
                    handleTriggerAction(
                      `Draft a formal technical document report based on ${docName}, formatted with executive summary, methodology, implementation details, and references.`,
                      true
                    )
                  }
                >
                  ⚡ Draft Technical Report Now
                </button>
                <button
                  className="btn-tool-secondary full"
                  onClick={() =>
                    handleTriggerAction(
                      `Draft a formal technical document report based on ${docName}, formatted with executive summary, methodology, implementation details, and references.`,
                      false
                    )
                  }
                >
                  Insert Prompt into Chat Input
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
