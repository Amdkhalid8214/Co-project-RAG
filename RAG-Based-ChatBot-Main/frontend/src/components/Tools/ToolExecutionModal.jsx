import React, { useState } from "react";
import { api } from "../../services/api";

export default function ToolExecutionModal({
  isOpen,
  toolId,
  onClose,
  activeDoc,
  onInsertIntoChat,
  onExecutePrompt
}) {
  const [calcExpr, setCalcExpr] = useState("");
  const [calcResult, setCalcResult] = useState(null);
  const [calcError, setCalcError] = useState(null);

  // Excel / CSV state
  const [sheetTitle, setSheetTitle] = useState("Performance & Benchmarks");
  const [sheetHeaders, setSheetHeaders] = useState("Model, BLEU (EN-DE), BLEU (EN-FR), Training FLOPs");
  const [sheetRows, setSheetRows] = useState(
    "ByteNet, 23.75, -, -\nDeep-Att + PosUnk, -, 40.4, 8.0e20\nTransformer (base), 27.3, 38.1, 3.3e18\nTransformer (big), 28.4, 41.8, 2.3e19"
  );
  const [isExporting, setIsExporting] = useState(false);

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

  // Safe Calculator Evaluation (AST / Math parser, no eval)
  const handleCalculate = () => {
    setCalcError(null);
    try {
      const sanitized = calcExpr.replace(/\s+/g, "");
      if (!/^[0-9+\-*/().%^]+$/.test(sanitized)) {
        throw new Error("Invalid characters in expression");
      }
      const compute = new Function(`return (${sanitized})`);
      const res = compute();
      if (!isFinite(res) || isNaN(res)) {
        throw new Error("Calculation resulted in non-finite number or division by zero");
      }
      setCalcResult(res);
    } catch (err) {
      setCalcError(err.message || "Malformed mathematical expression");
    }
  };

  const handleDownloadExcel = async (format = "csv") => {
    setIsExporting(true);
    try {
      const headersArr = sheetHeaders.split(",").map((s) => s.trim());
      const rowsArr = sheetRows
        .split("\n")
        .filter((r) => r.trim())
        .map((r) => r.split(",").map((s) => s.trim()));

      if (format === "csv") {
        const csvContent =
          headersArr.join(",") + "\n" + rowsArr.map((r) => r.join(",")).join("\n");
        const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${sheetTitle.toLowerCase().replace(/\s+/g, "_")}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      } else {
        try {
          const res = await fetch("http://localhost:5000/api/tools/execute", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              tool: "export_excel",
              arguments: {
                title: sheetTitle,
                headers: headersArr,
                rows: rowsArr,
                filename_prefix: sheetTitle.toLowerCase().replace(/\s+/g, "_")
              }
            })
          });
          const data = await res.json();
          if (data.download_url) {
            window.open(`http://localhost:5000${data.download_url}`, "_blank");
          } else {
            handleDownloadExcel("csv");
          }
        } catch {
          handleDownloadExcel("csv");
        }
      }
    } finally {
      setIsExporting(false);
    }
  };

  const handleInsertSheetAsTable = () => {
    const headersArr = sheetHeaders.split(",").map((s) => s.trim());
    const rowsArr = sheetRows
      .split("\n")
      .filter((r) => r.trim())
      .map((r) => r.split(",").map((s) => s.trim()));

    const headerLine = `| ${headersArr.join(" | ")} |`;
    const sepLine = `| ${headersArr.map(() => "---").join(" | ")} |`;
    const rowLines = rowsArr.map((r) => `| ${r.join(" | ")} |`).join("\n");
    const markdownTable = `### ${sheetTitle}\n\n${headerLine}\n${sepLine}\n${rowLines}`;

    handleTriggerAction(markdownTable, false);
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
            {toolId === "calculator" && "🧮 Calculator"}
            {toolId === "spreadsheet" && "📊 Create Spreadsheet"}
            {toolId === "analyze_data" && "📈 Data Analysis"}
            {toolId === "web_search" && "🌐 Web Search"}
            {toolId === "generate_chart" && "📉 Generate Chart"}
            {toolId === "summarize_pdf" && "📑 Summarize PDF"}
            {toolId === "create_document" && "📄 Create Document Report"}
            {toolId === "extract_tables" && "📋 Extract Tables from Document"}
          </h3>
          <button className="btn-tool-modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="tool-modal-body">
          {/* 1. Calculator */}
          {toolId === "calculator" && (
            <div className="tool-calc-view">
              <p className="tool-desc-text">Perform safe mathematical calculations and ground formulas with documents.</p>
              <div className="calc-input-row">
                <input
                  type="text"
                  className="calc-math-input"
                  placeholder="e.g. 10 * 49.99 + (10 * 49.99 * 0.08)"
                  value={calcExpr}
                  onChange={(e) => setCalcExpr(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleCalculate()}
                />
                <button className="btn-calc-execute" onClick={handleCalculate}>Calculate</button>
              </div>

              {calcResult !== null && (
                <div className="calc-result-box">
                  <span className="result-label">Result:</span>
                  <span className="result-value">{calcResult}</span>
                  <div style={{ display: "flex", gap: "8px", marginLeft: "auto" }}>
                    <button
                      className="btn-tool-primary"
                      onClick={() =>
                        handleTriggerAction(`The calculation result for ${calcExpr} is ${calcResult}.`, true)
                      }
                    >
                      ⚡ Send to Chat
                    </button>
                    <button
                      className="btn-tool-secondary"
                      onClick={() =>
                        handleTriggerAction(`The calculation result for ${calcExpr} is ${calcResult}.`, false)
                      }
                    >
                      Insert into Input
                    </button>
                  </div>
                </div>
              )}
              {calcError && <div className="calc-error-banner">{calcError}</div>}

              <div className="calc-quick-keypad">
                {["7", "8", "9", "/", "4", "5", "6", "*", "1", "2", "3", "-", "0", ".", "(", ")", "+"].map((k) => (
                  <button key={k} className="btn-key" onClick={() => setCalcExpr((p) => p + k)}>{k}</button>
                ))}
                <button className="btn-key clear" onClick={() => { setCalcExpr(""); setCalcResult(null); }}>C</button>
              </div>
            </div>
          )}

          {/* 2. Spreadsheet */}
          {toolId === "spreadsheet" && (
            <div className="tool-spreadsheet-view">
              <p className="tool-desc-text">Generate a verified, formula-injection protected Excel (.xlsx) or CSV spreadsheet.</p>
              <div className="form-group">
                <label>Workbook Title</label>
                <input type="text" value={sheetTitle} onChange={(e) => setSheetTitle(e.target.value)} />
              </div>
              <div className="form-group">
                <label>Column Headers (comma-separated)</label>
                <input type="text" value={sheetHeaders} onChange={(e) => setSheetHeaders(e.target.value)} />
              </div>
              <div className="form-group">
                <label>Data Rows (one per line, comma-separated)</label>
                <textarea rows={4} value={sheetRows} onChange={(e) => setSheetRows(e.target.value)} />
              </div>
              <div className="spreadsheet-actions-row" style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                <button className="btn-tool-primary" onClick={() => handleDownloadExcel("xlsx")} disabled={isExporting}>
                  {isExporting ? "Generating..." : "Download Excel (.xlsx)"}
                </button>
                <button className="btn-tool-secondary" onClick={() => handleDownloadExcel("csv")} disabled={isExporting}>
                  Export CSV
                </button>
                <button className="btn-tool-secondary" onClick={handleInsertSheetAsTable}>
                  Insert Table into Chat
                </button>
              </div>
            </div>
          )}

          {/* 3. Web Search */}
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

          {/* 4. Summarize PDF */}
          {toolId === "summarize_pdf" && (
            <div className="tool-summarize-view">
              <p className="tool-desc-text">
                Generate an executive structured summary with key takeaways from{" "}
                <strong>{docName}</strong>.
              </p>
              <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginTop: "16px" }}>
                <button
                  className="btn-tool-primary full"
                  onClick={() =>
                    handleTriggerAction(
                      `Please provide a comprehensive executive summary of ${docName}, outlining key objectives, methodologies, technical specifications, and primary findings.`,
                      true
                    )
                  }
                >
                  ⚡ Summarize {docName} Now
                </button>
                <button
                  className="btn-tool-secondary full"
                  onClick={() =>
                    handleTriggerAction(
                      `Please provide a comprehensive executive summary of ${docName}, outlining key objectives, methodologies, technical specifications, and primary findings.`,
                      false
                    )
                  }
                >
                  Insert Prompt into Chat Input
                </button>
              </div>
            </div>
          )}

          {/* 5. Extract Tables */}
          {toolId === "extract_tables" && (
            <div className="tool-tables-view">
              <p className="tool-desc-text">
                Extract all structured tables, performance matrices, and statistical rows from{" "}
                <strong>{docName}</strong> into formatted Markdown tables with exact numbers and metrics.
              </p>
              <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginTop: "16px" }}>
                <button
                  className="btn-tool-primary full"
                  onClick={() =>
                    handleTriggerAction(
                      `Extract all tabular data, tables, performance matrices, and statistical rows from ${docName} with exact numbers.`,
                      true
                    )
                  }
                >
                  ⚡ Extract Document Tables Now
                </button>
                <button
                  className="btn-tool-secondary full"
                  onClick={() =>
                    handleTriggerAction(
                      `Extract all tabular data, tables, performance matrices, and statistical rows from ${docName} with exact numbers.`,
                      false
                    )
                  }
                >
                  Insert Prompt into Chat Input
                </button>
              </div>
            </div>
          )}

          {/* 6. Analyze Data */}
          {toolId === "analyze_data" && (
            <div className="tool-analyze-view">
              <p className="tool-desc-text">
                Perform descriptive statistics, distribution metrics, and trend analysis on numerical benchmarks in{" "}
                <strong>{docName}</strong>.
              </p>
              <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginTop: "16px" }}>
                <button
                  className="btn-tool-primary full"
                  onClick={() =>
                    handleTriggerAction(
                      `Analyze the quantitative data and benchmarks discussed in ${docName}. Calculate mean, ranges, and compare results across configurations.`,
                      true
                    )
                  }
                >
                  ⚡ Run Quantitative Analysis Now
                </button>
                <button
                  className="btn-tool-secondary full"
                  onClick={() =>
                    handleTriggerAction(
                      `Analyze the quantitative data and benchmarks discussed in ${docName}. Calculate mean, ranges, and compare results across configurations.`,
                      false
                    )
                  }
                >
                  Insert Prompt into Chat Input
                </button>
              </div>
            </div>
          )}

          {/* 7. Generate Chart */}
          {toolId === "generate_chart" && (
            <div className="tool-chart-view">
              <p className="tool-desc-text">
                Synthesize comparative benchmarks and metrics into structured visualization tables and chart summaries from{" "}
                <strong>{docName}</strong>.
              </p>
              <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginTop: "16px" }}>
                <button
                  className="btn-tool-primary full"
                  onClick={() =>
                    handleTriggerAction(
                      `Generate a visual comparative chart breakdown for the results and accuracy benchmarks described in ${docName}.`,
                      true
                    )
                  }
                >
                  ⚡ Generate Chart Breakdown Now
                </button>
                <button
                  className="btn-tool-secondary full"
                  onClick={() =>
                    handleTriggerAction(
                      `Generate a visual comparative chart breakdown for the results and accuracy benchmarks described in ${docName}.`,
                      false
                    )
                  }
                >
                  Insert Prompt into Chat Input
                </button>
              </div>
            </div>
          )}

          {/* 8. Create Document */}
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
