import React, { useRef, useEffect, useCallback, useState } from "react";

const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:5000/api";

export default function PdfViewerDrawer({
  isOpen,
  onClose,
  document: doc,
  currentPage,
  setCurrentPage,
  activeHighlights,
  focusedCitationIndex,
  getAuthHeaders
}) {
  const [totalPages, setTotalPages] = useState(1);
  const [zoomScale, setZoomScale] = useState(1.1);
  const [pdfDoc, setPdfDoc] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const canvasRef = useRef(null);
  const renderTaskRef = useRef(null);

  // Load PDF Document
  useEffect(() => {
    if (!doc || !isOpen) return;
    let isCancelled = false;
    setIsLoading(true);

    const loadDoc = async () => {
      if (!window.pdfjsLib) {
        console.warn("window.pdfjsLib is not loaded yet.");
        setIsLoading(false);
        return;
      }

      try {
        const fileUrl = `${API_BASE}/documents/${doc.id}/file`;
        const loadingTask = window.pdfjsLib.getDocument({
          url: fileUrl,
          httpHeaders: getAuthHeaders ? getAuthHeaders() : {}
        });
        const loadedPdf = await loadingTask.promise;
        if (!isCancelled) {
          setPdfDoc(loadedPdf);
          setTotalPages(loadedPdf.numPages);
          setIsLoading(false);
        }
      } catch (e) {
        console.error("PDF.js load error:", e);
        setIsLoading(false);
      }
    };

    loadDoc();
    return () => {
      isCancelled = true;
    };
  }, [doc, isOpen, getAuthHeaders]);

  // Render Page with Virtualized Canvas Cleanup
  const renderPage = useCallback(async (pdf, pageNum) => {
    if (!pdf || !canvasRef.current) return;

    // Cancel existing render task to prevent canvas race conditions
    if (renderTaskRef.current) {
      try {
        renderTaskRef.current.cancel();
      } catch {}
    }

    try {
      const page = await pdf.getPage(pageNum);
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");

      const viewport = page.getViewport({ scale: zoomScale });
      canvas.width = viewport.width;
      canvas.height = viewport.height;

      // Clean canvas before redraw
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const renderContext = {
        canvasContext: ctx,
        viewport: viewport
      };

      const task = page.render(renderContext);
      renderTaskRef.current = task;
      await task.promise;
    } catch (e) {
      if (e?.name !== "RenderingCancelledException") {
        console.error("PDF render error:", e);
      }
    }
  }, [zoomScale]);

  useEffect(() => {
    if (pdfDoc && isOpen) {
      renderPage(pdfDoc, currentPage);
    }
  }, [pdfDoc, currentPage, zoomScale, isOpen, renderPage]);

  if (!isOpen) return null;

  return (
    <aside className="pdf-viewer-drawer open">
      <div className="pdf-toolbar">
        <div className="pdf-toolbar-left">
          <span className="pdf-doc-title" title={doc?.filename}>{doc?.filename || "Document Viewer"}</span>
        </div>

        <div className="pdf-toolbar-center">
          <button
            className="btn-toolbar-nav"
            onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
            disabled={currentPage <= 1}
            title="Previous Page"
          >
            ◀
          </button>
          <span className="page-counter">
            {currentPage} / {totalPages}
          </span>
          <button
            className="btn-toolbar-nav"
            onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
            disabled={currentPage >= totalPages}
            title="Next Page"
          >
            ▶
          </button>
        </div>

        <div className="pdf-toolbar-right">
          <button
            className="btn-toolbar-zoom"
            onClick={() => setZoomScale((z) => Math.max(0.6, z - 0.15))}
            title="Zoom Out"
          >
            -
          </button>
          <span className="zoom-percentage">{Math.round(zoomScale * 100)}%</span>
          <button
            className="btn-toolbar-zoom"
            onClick={() => setZoomScale((z) => Math.min(2.5, z + 0.15))}
            title="Zoom In"
          >
            +
          </button>
          <button className="btn-toolbar-close" onClick={onClose} title="Close PDF">
            ✕
          </button>
        </div>
      </div>

      <div className="pdf-canvas-container">
        {isLoading && <div className="pdf-loading-spinner">Loading PDF...</div>}
        {doc ? (
          <div className="viewer-page-container">
            <canvas ref={canvasRef} />
            <div className="highlights-overlay">
              {activeHighlights
                .filter((b) => (b.page || 1) === currentPage)
                .map((box, bIdx) => {
                  const canvas = canvasRef.current;
                  const cWidth = canvas ? canvas.width : 600;
                  const cHeight = canvas ? canvas.height : 800;
                  const pWidth = box.page_width || 612;
                  const pHeight = box.page_height || 792;

                  const scaleX = cWidth / pWidth;
                  const scaleY = cHeight / pHeight;

                  const top =
                    box.coord_origin === "BOTTOMLEFT"
                      ? (pHeight - box.y1) * scaleY
                      : box.y0 * scaleY;
                  const height = Math.abs(box.y1 - box.y0) * scaleY;
                  const left = box.x0 * scaleX;
                  const width = Math.abs(box.x1 - box.x0) * scaleX;

                  return (
                    <div
                      key={bIdx}
                      className="highlight-rect focused"
                      style={{
                        top: `${top}px`,
                        left: `${left}px`,
                        width: `${Math.max(16, width)}px`,
                        height: `${Math.max(12, height)}px`
                      }}
                      title={`Citation [${focusedCitationIndex || ""}]`}
                    />
                  );
                })}
            </div>
          </div>
        ) : (
          <div className="no-pdf-selected">Select a document or click a citation [n] to inspect evidence.</div>
        )}
      </div>
    </aside>
  );
}
