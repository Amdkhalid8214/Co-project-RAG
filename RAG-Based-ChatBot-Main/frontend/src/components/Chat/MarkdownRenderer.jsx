import React from "react";

/**
 * Parses inline formatting:
 * - Citations: [1], [2], [1, 2], [1, 2, 3]
 * - Bold: **text** or __text__
 * - Inline Code: `text`
 * - Links: [label](url)
 * - Italic: *text* or _text_
 */
function renderInline(text, citations, onCitationClick) {
  if (!text) return null;

  // Split text by recognized markdown inline tokens
  const tokenRegex = /(\[\d+(?:,\s*\d+)*\]|\*\*[^*]+?\*\*|__[^_]+?__|`[^`]+?`|\[[^\]]+\]\([^)]+\)|\*[^*]+?\*|_[^_]+?_)/g;
  const parts = text.split(tokenRegex);

  return parts.map((part, idx) => {
    if (!part) return null;

    // 1. Inline Citation Markers [1], [2], [1, 2]
    const citeMatch = part.match(/^\[(\d+(?:,\s*\d+)*)\]$/);
    if (citeMatch) {
      const numbers = citeMatch[1]
        .split(",")
        .map((s) => parseInt(s.trim(), 10))
        .filter((n) => !isNaN(n));

      return (
        <span key={idx} className="inline-citations-wrapper">
          {numbers.map((num, nIdx) => {
            const matchedCite = Array.isArray(citations)
              ? citations.find((c) => Number(c.source_index) === num)
              : null;
            return (
              <button
                key={nIdx}
                type="button"
                className="inline-citation-pill"
                onClick={(e) => {
                  e.stopPropagation();
                  if (onCitationClick) {
                    onCitationClick(num, matchedCite);
                  }
                }}
                title={
                  matchedCite
                    ? `${matchedCite.filename || "Document"} • Page ${matchedCite.page || matchedCite.page_number || 1}`
                    : `Source [${num}]`
                }
              >
                [{num}]
              </button>
            );
          })}
        </span>
      );
    }

    // 2. Bold Text **bold** or __bold__
    if (
      (part.startsWith("**") && part.endsWith("**") && part.length >= 4) ||
      (part.startsWith("__") && part.endsWith("__") && part.length >= 4)
    ) {
      const inner = part.slice(2, -2);
      // Guard against LLMs wrapping an entire long narrative paragraph in **...**
      if (inner.length > 100 && inner.includes(". ")) {
        const colonIdx = inner.indexOf(":");
        const dotIdx = inner.indexOf(". ");
        const splitIdx =
          colonIdx !== -1 && colonIdx < 50
            ? colonIdx + 1
            : dotIdx !== -1 && dotIdx < 50
            ? dotIdx + 1
            : -1;
        if (splitIdx !== -1) {
          const boldPrefix = inner.slice(0, splitIdx);
          const normalRest = inner.slice(splitIdx);
          return (
            <React.Fragment key={idx}>
              <strong className="md-bold">
                {renderInline(boldPrefix, citations, onCitationClick)}
              </strong>
              {renderInline(normalRest, citations, onCitationClick)}
            </React.Fragment>
          );
        }
      }
      return (
        <strong key={idx} className="md-bold">
          {renderInline(inner, citations, onCitationClick)}
        </strong>
      );
    }

    // 3. Inline Code `code`
    if (part.startsWith("`") && part.endsWith("`") && part.length >= 2) {
      return (
        <code key={idx} className="md-inline-code">
          {part.slice(1, -1)}
        </code>
      );
    }

    // 4. Markdown Link [label](url)
    const linkMatch = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
    if (linkMatch) {
      return (
        <a
          key={idx}
          href={linkMatch[2]}
          target="_blank"
          rel="noopener noreferrer"
          className="md-link"
        >
          {linkMatch[1]}
        </a>
      );
    }

    // 5. Italic Text *italic* or _italic_
    if (
      (part.startsWith("*") && part.endsWith("*") && part.length >= 2) ||
      (part.startsWith("_") && part.endsWith("_") && part.length >= 2)
    ) {
      const inner = part.slice(1, -1);
      return (
        <em key={idx} className="md-italic">
          {renderInline(inner, citations, onCitationClick)}
        </em>
      );
    }

    // Default plain text
    return part;
  });
}

/**
 * Groups lines into structured block elements:
 * - Headings (H1 - H6) with leading #, ##, ###, #### completely removed & styled bold
 * - Code blocks (```lang ... ```)
 * - Tables (| col1 | col2 |)
 * - Lists (ul: -, *, •; ol: 1., 2.)
 * - Blockquotes (> ...)
 * - Horizontal rules (---, ***)
 * - Paragraphs (<p>)
 */
function parseMarkdownBlocks(content) {
  if (!content) return [];

  const rawLines = content.replace(/\r\n/g, "\n").split("\n");
  const blocks = [];
  let i = 0;

  while (i < rawLines.length) {
    let line = rawLines[i];
    const trimmed = line.trim();

    // Skip empty lines
    if (!trimmed) {
      i++;
      continue;
    }

    // Strip leading [TABLE] tag if Docling/worker prepended it
    if (trimmed.startsWith("[TABLE]")) {
      line = trimmed.replace(/^\[TABLE\]\s*/, "");
      if (!line) {
        i++;
        continue;
      }
    }

    // 1. Code Block: ```[lang]
    if (line.trim().startsWith("```")) {
      const lang = line.trim().slice(3).trim();
      const codeLines = [];
      i++;
      while (i < rawLines.length && !rawLines[i].trim().startsWith("```")) {
        codeLines.push(rawLines[i]);
        i++;
      }
      if (i < rawLines.length) i++; // Consume closing ```
      blocks.push({
        type: "code",
        language: lang,
        content: codeLines.join("\n"),
      });
      continue;
    }

    // 2. Headings: #, ##, ###, ####, #####, ######
    // Matches heading markers with or without space, e.g. "### Positional Encoding"
    const headingMatch = line.match(/^(#{1,6})\s*(.+)$/);
    if (headingMatch) {
      const level = headingMatch[1].length;
      // Strip leading hashes completely and any trailing hashes (e.g. "### Title ###")
      const headingText = headingMatch[2].trim().replace(/\s+#+$/, "");

      // Strict heading detection: Only true short titles should be bold headings.
      // If a line is a long narrative paragraph (> 85 chars, or > 45 chars containing sentence periods),
      // it is body text that was prefixed with hashes by the LLM. Render as normal regular-weight paragraph!
      const isActuallyParagraph =
        headingText.length > 85 ||
        (headingText.length > 45 && headingText.includes(". ")) ||
        (headingText.length > 55 && headingText.endsWith("."));

      if (isActuallyParagraph) {
        blocks.push({
          type: "paragraph",
          text: headingText,
        });
        i++;
        continue;
      }

      blocks.push({
        type: "heading",
        level,
        text: headingText,
      });
      i++;
      continue;
    }

    // 3. Horizontal Rule: --- or *** or ___
    if (/^(?:---|\*\*\*|___)\s*$/.test(trimmed)) {
      blocks.push({ type: "hr" });
      i++;
      continue;
    }

    // 4. Blockquote: > text
    if (trimmed.startsWith(">")) {
      const quoteLines = [];
      while (i < rawLines.length && rawLines[i].trim().startsWith(">")) {
        quoteLines.push(rawLines[i].trim().replace(/^>\s?/, ""));
        i++;
      }
      blocks.push({
        type: "blockquote",
        text: quoteLines.join("\n"),
      });
      continue;
    }

    // 5. Tables: lines starting and ending with |
    if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
      const tableLines = [];
      while (
        i < rawLines.length &&
        rawLines[i].trim().startsWith("|") &&
        rawLines[i].trim().endsWith("|")
      ) {
        tableLines.push(rawLines[i].trim());
        i++;
      }

      if (tableLines.length >= 1) {
        const parseRow = (rowStr) =>
          rowStr
            .split("|")
            .slice(1, -1)
            .map((c) => c.trim());

        const headerCells = parseRow(tableLines[0]);
        let dataRows = [];
        let alignments = [];

        // Check if row 2 is a markdown divider line: | --- | :---: | ---: |
        if (tableLines.length >= 2 && /^\|[\s\-:]+(\|[\s\-:]+)+\|$/.test(tableLines[1])) {
          const alignCells = parseRow(tableLines[1]);
          alignments = alignCells.map((cell) => {
            if (cell.startsWith(":") && cell.endsWith(":")) return "center";
            if (cell.endsWith(":")) return "right";
            return "left";
          });
          dataRows = tableLines.slice(2).map(parseRow);
        } else {
          dataRows = tableLines.slice(1).map(parseRow);
        }

        blocks.push({
          type: "table",
          headers: headerCells,
          alignments,
          rows: dataRows,
        });
        continue;
      }
    }

    // 6. Unordered List: - item, * item, • item, + item
    const ulMatch = line.match(/^(\s*)([-*•]|\+)\s+(.+)$/);
    if (ulMatch) {
      const items = [];
      while (i < rawLines.length) {
        const itemMatch = rawLines[i].match(/^(\s*)([-*•]|\+)\s+(.+)$/);
        if (!itemMatch) break;
        items.push(itemMatch[3]);
        i++;
      }
      blocks.push({
        type: "ul",
        items,
      });
      continue;
    }

    // 7. Ordered List: 1. item, 2. item
    const olMatch = line.match(/^(\s*)(\d+)[.)]\s+(.+)$/);
    if (olMatch) {
      const items = [];
      while (i < rawLines.length) {
        const itemMatch = rawLines[i].match(/^(\s*)(\d+)[.)]\s+(.+)$/);
        if (!itemMatch) break;
        items.push(itemMatch[3]);
        i++;
      }
      blocks.push({
        type: "ol",
        items,
      });
      continue;
    }

    // 8. Standard Paragraph: collects consecutive non-block lines
    const paraLines = [];
    while (
      i < rawLines.length &&
      rawLines[i].trim() &&
      !rawLines[i].trim().startsWith("#") &&
      !rawLines[i].trim().startsWith("```") &&
      !rawLines[i].trim().startsWith(">") &&
      !(rawLines[i].trim().startsWith("|") && rawLines[i].trim().endsWith("|")) &&
      !rawLines[i].match(/^(\s*)([-*•]|\+|\d+[.)])\s+/)
    ) {
      paraLines.push(rawLines[i]);
      i++;
    }

    if (paraLines.length > 0) {
      blocks.push({
        type: "paragraph",
        text: paraLines.join(" "),
      });
    } else {
      // Fallback advance if nothing matched to guarantee progression
      blocks.push({
        type: "paragraph",
        text: line,
      });
      i++;
    }
  }

  return blocks;
}

export default function MarkdownRenderer({ content, citations, onCitationClick }) {
  if (!content) return null;

  const blocks = parseMarkdownBlocks(content);

  // Filter and deduplicate genuine citations
  const seenCites = new Set();
  const validCitations = (Array.isArray(citations) ? citations : []).filter((c) => {
    if (!c) return false;
    const isDoc = Boolean((c.filename || c.doc_id || c.page) && c.type !== "web");
    const isWeb = Boolean(c.type === "web" || c.url);
    if (!isDoc && !isWeb) return false;

    // Deduplication key: keeps distinct chunks even if from same page
    const key = c.chunk_id
      ? `${c.doc_id || c.filename}_chunk_${c.chunk_id}`
      : `${c.doc_id || c.filename}_p${c.page || c.page_number || 1}_s${c.source_index || 0}_${c.url || ""}`;

    if (seenCites.has(key)) return false;
    seenCites.add(key);
    return true;
  });

  return (
    <div className="markdown-content">
      {blocks.map((block, idx) => {
        switch (block.type) {
          case "heading": {
            // Render actual heading element with brode/bold styling and without raw '#'
            const HeadingTag = `h${Math.min(block.level, 6)}`;
            const headingClass = `md-heading md-h${block.level}`;
            return (
              <HeadingTag key={idx} className={headingClass}>
                {renderInline(block.text, citations, onCitationClick)}
              </HeadingTag>
            );
          }

          case "paragraph":
            return (
              <p key={idx} className="md-paragraph">
                {renderInline(block.text, citations, onCitationClick)}
              </p>
            );

          case "ul":
            return (
              <ul key={idx} className="md-ul">
                {block.items.map((item, itemIdx) => (
                  <li key={itemIdx} className="md-li">
                    {renderInline(item, citations, onCitationClick)}
                  </li>
                ))}
              </ul>
            );

          case "ol":
            return (
              <ol key={idx} className="md-ol">
                {block.items.map((item, itemIdx) => (
                  <li key={itemIdx} className="md-li">
                    {renderInline(item, citations, onCitationClick)}
                  </li>
                ))}
              </ol>
            );

          case "blockquote":
            return (
              <blockquote key={idx} className="md-blockquote">
                {renderInline(block.text, citations, onCitationClick)}
              </blockquote>
            );

          case "hr":
            return <hr key={idx} className="md-hr" />;

          case "code":
            return (
              <div key={idx} className="md-code-block-container">
                {block.language && (
                  <div className="md-code-block-header">{block.language}</div>
                )}
                <pre className="md-code-block-pre">
                  <code>{block.content}</code>
                </pre>
              </div>
            );

          case "table":
            return (
              <div key={idx} className="md-table-wrapper">
                <table className="md-table">
                  <thead>
                    <tr>
                      {block.headers.map((h, hIdx) => (
                        <th
                          key={hIdx}
                          style={{ textAlign: block.alignments[hIdx] || "left" }}
                        >
                          {renderInline(h, citations, onCitationClick)}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {block.rows.map((row, rIdx) => (
                      <tr key={rIdx}>
                        {row.map((cell, cIdx) => (
                          <td
                            key={cIdx}
                            style={{ textAlign: block.alignments[cIdx] || "left" }}
                          >
                            {renderInline(cell, citations, onCitationClick)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            );

          default:
            return null;
        }
      })}

      {/* Restored Evidence / Source Citation Cards Stack */}
      {validCitations.length > 0 && (
        <div className="citations-stack">
          {validCitations.map((cite, i) => {
            const isWeb = cite.type === "web" || cite.url;
            const srcIdx = cite.source_index != null ? cite.source_index : i + 1;
            const pageNum = cite.page || cite.page_number || 1;
            const docName = cite.filename || cite.doc_name || cite.title || "Document";

            if (isWeb) {
              let host = "";
              try {
                if (cite.url) host = new URL(cite.url).hostname.replace(/^www\./, "");
              } catch {}

              return (
                <a
                  key={`web-cite-${i}-${srcIdx}`}
                  href={cite.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="citation-card-item web-citation-card"
                  title={cite.snippet || cite.title || cite.url}
                >
                  <div className="citation-card-left">
                    <svg
                      className="citation-doc-icon web-icon"
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <circle cx="12" cy="12" r="10" />
                      <line x1="2" y1="12" x2="22" y2="12" />
                      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                    </svg>
                    <span className="citation-source-num">[{srcIdx}]</span>
                    <span className="citation-doc-name">{docName}</span>
                    {host && (
                      <>
                        <span className="citation-separator">•</span>
                        <span className="citation-page-num">{host}</span>
                      </>
                    )}
                  </div>
                  <span className="citation-chevron">↗</span>
                </a>
              );
            }

            return (
              <button
                key={`doc-cite-${i}-${srcIdx}`}
                type="button"
                className="citation-card-item"
                onClick={() => {
                  if (onCitationClick) {
                    onCitationClick(srcIdx, cite);
                  }
                }}
                title={
                  cite.snippet
                    ? `Page ${pageNum} • "${cite.snippet.slice(0, 100)}..."`
                    : `Navigate to ${docName} (Page ${pageNum})`
                }
              >
                <div className="citation-card-left">
                  <svg
                    className="citation-doc-icon"
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                  </svg>
                  <span className="citation-source-num">[{srcIdx}]</span>
                  <span className="citation-doc-name">{docName}</span>
                  <span className="citation-separator">•</span>
                  <span className="citation-page-num">p. {pageNum}</span>
                </div>
                <span className="citation-chevron">›</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
