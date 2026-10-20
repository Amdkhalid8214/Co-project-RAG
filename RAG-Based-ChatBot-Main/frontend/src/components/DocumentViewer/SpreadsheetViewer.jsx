import React, { useState, useEffect, useCallback, useMemo } from "react";
import { api } from "../../services/api";

const API_BASE = "http://localhost:5000/api";

export default function SpreadsheetViewer({
  document: doc,
  viewMode,
  onToggleMaximize,
  onCloseViewer,
  onToggleSplitView
}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeSheet, setActiveSheet] = useState(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [searchTerm, setSearchTerm] = useState("");

  const docTitle = doc?.filename || "Spreadsheet";
  const docId = doc?.id;
  const fileExt = (doc?.file_type || doc?.filename?.split(".").pop() || "xlsx").toUpperCase();

  const fetchSheetData = useCallback(
    async (targetSheet = null, targetPage = 1, targetPageSize = pageSize) => {
      if (!docId) return;
      setLoading(true);
      setError(null);
      try {
        const res = await api.getSpreadsheetData(docId, targetSheet, targetPage, targetPageSize);
        setData(res);
        setActiveSheet(res.active_sheet);
        setPage(res.page);
      } catch (err) {
        console.error("Error fetching spreadsheet data:", err);
        setError(err.message || "Failed to load spreadsheet data.");
      } finally {
        setLoading(false);
      }
    },
    [docId, pageSize]
  );

  useEffect(() => {
    fetchSheetData(null, 1, pageSize);
  }, [fetchSheetData, pageSize]);

  const handleSheetChange = (sheetName) => {
    if (sheetName === activeSheet) return;
    setSearchTerm("");
    fetchSheetData(sheetName, 1, pageSize);
  };

  const handlePageChange = (newPage) => {
    if (!data) return;
    const maxPages = data.total_pages || 1;
    const valid = Math.max(1, Math.min(maxPages, newPage));
    fetchSheetData(activeSheet, valid, pageSize);
  };

  const handleDownloadOriginal = () => {
    if (!docId) return;
    const token = localStorage.getItem("docuchat_token");
    const authQuery = token ? `?token=${encodeURIComponent(token)}` : "";
    window.open(`${API_BASE}/documents/${docId}/file${authQuery}`, "_blank");
  };

  // Filter rows locally if searchTerm exists
  const displayRows = useMemo(() => {
    if (!data?.rows) return [];
    if (!searchTerm.trim()) return data.rows;
    const q = searchTerm.toLowerCase();
    return data.rows.filter((row) =>
      row.some((cell) => String(cell ?? "").toLowerCase().includes(q))
    );
  }, [data?.rows, searchTerm]);

  // Helper for Excel column letters A, B, C...
  const getColLetter = (index) => {
    let letter = "";
    let temp = index;
    while (temp >= 0) {
      letter = String.fromCharCode((temp % 26) + 65) + letter;
      temp = Math.floor(temp / 26) - 1;
    }
    return letter;
  };

  const isNumeric = (val) => {
    if (typeof val === "number") return true;
    if (typeof val !== "string" || val.trim() === "") return false;
    return !isNaN(Number(val.replace(/,/g, "")));
  };

  const formatCell = (val) => {
    if (val === null || val === undefined || val === "") {
      return <span className="spreadsheet-cell-empty">—</span>;
    }
    return String(val);
  };

  const rowStartIndex = (page - 1) * pageSize;

  return (
    <aside className="chatgpt-side-document-panel spreadsheet-panel">
      {/* Top Toolbar */}
      <div className="doc-viewer-top-toolbar spreadsheet-top-toolbar">
        {/* Left: Excel icon + Title + Sheet metadata */}
        <div className="doc-toolbar-left-meta">
          <div className="spreadsheet-icon-badge" title="Excel Spreadsheet">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="8" y1="13" x2="16" y2="13" />
              <line x1="8" y1="17" x2="16" y2="17" />
              <polyline points="10 9 9 9 8 9" />
            </svg>
          </div>
          <div className="doc-title-stack">
            <span className="doc-toolbar-filename" title={docTitle}>
              {docTitle}
            </span>
            <span className="doc-toolbar-pagesub">
              {data ? (
                <>
                  <span className="spreadsheet-format-tag">{fileExt}</span>
                  <span className="spreadsheet-meta-divider">•</span>
                  <span>{data.total_rows} rows, {data.total_columns} cols</span>
                  {data.dimensions && data.dimensions !== "None" && (
                    <>
                      <span className="spreadsheet-meta-divider">•</span>
                      <span className="spreadsheet-dim-tag">{data.dimensions}</span>
                    </>
                  )}
                </>
              ) : (
                <span className="spreadsheet-format-tag">{fileExt}</span>
              )}
            </span>
          </div>
        </div>

        {/* Center: Search & Filter inside Sheet */}
        <div className="doc-toolbar-center-controls spreadsheet-center-controls">
          <div className="spreadsheet-search-box">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input
              type="text"
              className="spreadsheet-search-input"
              placeholder="Filter sheet rows..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            {searchTerm && (
              <button
                className="spreadsheet-search-clear"
                onClick={() => setSearchTerm("")}
                title="Clear filter"
              >
                ✕
              </button>
            )}
          </div>
        </div>

        {/* Right: Actions */}
        <div className="doc-toolbar-right-controls">
          <button
            className="btn-toolbar-icon"
            onClick={handleDownloadOriginal}
            title="Download Original File"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
          </button>

          <button
            className={`btn-toolbar-icon ${viewMode === "document" ? "btn-active" : ""}`}
            onClick={onToggleMaximize}
            title={viewMode === "document" ? "Restore Split View" : "Maximize Document Viewer"}
          >
            {viewMode === "document" ? (
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="4 14 10 14 10 20" />
                <polyline points="20 10 14 10 14 4" />
                <line x1="14" y1="10" x2="21" y2="3" />
                <line x1="3" y1="21" x2="10" y2="14" />
              </svg>
            ) : (
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="15 3 21 3 21 9" />
                <polyline points="9 21 3 21 3 15" />
                <line x1="21" y1="3" x2="14" y2="10" />
                <line x1="3" y1="21" x2="10" y2="14" />
              </svg>
            )}
          </button>

          <button
            className="btn-toolbar-icon btn-toolbar-close"
            onClick={onCloseViewer || onToggleSplitView}
            title="Close Viewer"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
      </div>

      {/* Sheet Selection Tab Bar (Excel Workbook Tabs) */}
      {data?.sheet_names && data.sheet_names.length > 0 && (
        <div className="spreadsheet-sheet-tabs-bar">
          <div className="spreadsheet-tabs-label">Worksheets:</div>
          <div className="spreadsheet-tabs-scroll">
            {data.sheet_names.map((sheet) => (
              <button
                key={sheet}
                className={`spreadsheet-tab-btn ${sheet === activeSheet ? "active" : ""}`}
                onClick={() => handleSheetChange(sheet)}
                title={`Switch to worksheet: ${sheet}`}
              >
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="3" width="18" height="18" rx="2" />
                  <line x1="3" y1="9" x2="21" y2="9" />
                  <line x1="9" y1="21" x2="9" y2="9" />
                </svg>
                <span>{sheet}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Main Table Stage */}
      <div className="spreadsheet-table-stage">
        {loading && (
          <div className="spreadsheet-loading-overlay">
            <div className="doc-spinner" />
            <span>Loading spreadsheet rows...</span>
          </div>
        )}

        {error && !loading && (
          <div className="doc-empty-state-card">
            <div className="doc-error-block">
              <div className="doc-error-icon">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
              </div>
              <h4 className="doc-error-title">Could not load spreadsheet data</h4>
              <p className="doc-error-desc">{error}</p>
              <div className="doc-error-actions">
                <button
                  className="btn-retry-doc"
                  onClick={() => fetchSheetData(activeSheet, page, pageSize)}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="1 4 1 10 7 10" />
                    <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
                  </svg>
                  Try Again
                </button>
                <button className="btn-download-orig" onClick={handleDownloadOriginal}>
                  Download Original
                </button>
              </div>
            </div>
          </div>
        )}

        {!error && !loading && data && (
          <>
            {data.columns.length === 0 || data.total_rows === 0 ? (
              <div className="spreadsheet-empty-sheet">
                <div className="spreadsheet-empty-icon">📊</div>
                <div className="spreadsheet-empty-title">This worksheet is empty</div>
                <div className="spreadsheet-empty-desc">
                  No tabular rows were found in worksheet &quot;{activeSheet}&quot;.
                </div>
              </div>
            ) : (
              <div className="spreadsheet-table-wrapper">
                <table className="spreadsheet-table">
                  <thead>
                    <tr>
                      {/* Top-left corner cell */}
                      <th className="spreadsheet-corner-header">#</th>
                      {data.columns.map((colName, cIdx) => (
                        <th key={cIdx} className="spreadsheet-col-header">
                          <span className="col-letter">{getColLetter(cIdx)}</span>
                          <span className="col-title" title={colName}>{colName}</span>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {displayRows.length === 0 ? (
                      <tr>
                        <td
                          colSpan={data.columns.length + 1}
                          className="spreadsheet-no-match-cell"
                        >
                          No rows match filter &quot;{searchTerm}&quot;
                        </td>
                      </tr>
                    ) : (
                      displayRows.map((row, rIdx) => {
                        const actualRowNumber = rowStartIndex + rIdx + 1;
                        return (
                          <tr key={rIdx} className="spreadsheet-row">
                            <td className="spreadsheet-row-number">{actualRowNumber}</td>
                            {data.columns.map((_, cIdx) => {
                              const cellVal = row[cIdx];
                              const num = isNumeric(cellVal);
                              return (
                                <td
                                  key={cIdx}
                                  className={`spreadsheet-cell ${num ? "cell-numeric" : ""}`}
                                  title={cellVal !== null && cellVal !== undefined ? String(cellVal) : ""}
                                >
                                  {formatCell(cellVal)}
                                </td>
                              );
                            })}
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </div>

      {/* Bottom Footer & Pagination Bar */}
      {data && !error && data.total_rows > 0 && (
        <div className="spreadsheet-footer-bar">
          <div className="spreadsheet-footer-left">
            <span>
              Showing {Math.min(data.total_rows, rowStartIndex + 1)}–
              {Math.min(data.total_rows, rowStartIndex + displayRows.length)} of {data.total_rows} rows
            </span>
            {searchTerm && (
              <span className="spreadsheet-filter-active-pill">
                Filtered from {data.rows?.length || 0}
              </span>
            )}
          </div>

          <div className="spreadsheet-footer-pagination">
            <div className="spreadsheet-page-size-selector">
              <span>Rows per page:</span>
              <select
                value={pageSize}
                onChange={(e) => {
                  const s = Number(e.target.value);
                  setPageSize(s);
                  fetchSheetData(activeSheet, 1, s);
                }}
              >
                <option value={25}>25</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
                <option value={200}>200</option>
              </select>
            </div>

            <div className="spreadsheet-pagination-nav">
              <button
                className="btn-page-nav"
                disabled={page <= 1}
                onClick={() => handlePageChange(page - 1)}
                title="Previous page"
              >
                ‹ Prev
              </button>
              <span className="spreadsheet-page-indicator">
                Page {page} of {data.total_pages || 1}
              </span>
              <button
                className="btn-page-nav"
                disabled={page >= (data.total_pages || 1)}
                onClick={() => handlePageChange(page + 1)}
                title="Next page"
              >
                Next ›
              </button>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}
