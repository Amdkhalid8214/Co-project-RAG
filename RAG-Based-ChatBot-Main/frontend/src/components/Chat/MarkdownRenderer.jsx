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

    // 1. Suppress Citation Pills and Evidence Numbers [1], [2], [1, 2]
    const citeMatch = part.match(/^\[(\d+(?:,\s*\d+)*)\]$/);
    if (citeMatch) {
      // Do not display inline evidence pills, buttons, or bracket numbers in chat UI
      return null;
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
    </div>
  );
}
