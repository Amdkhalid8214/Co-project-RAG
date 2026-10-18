import React, { useState } from "react";

export default function ProjectsModal({
  isOpen,
  onClose,
  projects,
  setProjects,
  activeProjectId,
  setActiveProjectId,
  documents = []
}) {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [selectedDocs, setSelectedDocs] = useState([]);

  if (!isOpen) return null;

  const handleCreate = (e) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    const newProj = {
      id: `proj_${Date.now()}`,
      title: newTitle.trim(),
      description: newDesc.trim() || "Custom AI Document Intelligence Workspace",
      doc_count: selectedDocs.length,
      doc_ids: selectedDocs,
      created_at: new Date().toLocaleDateString(),
    };

    setProjects((prev) => [newProj, ...prev]);
    setActiveProjectId(newProj.id);
    setNewTitle("");
    setNewDesc("");
    setSelectedDocs([]);
    setShowCreateForm(false);
  };

  const handleDelete = (projId) => {
    if (window.confirm("Delete this project workspace?")) {
      setProjects((prev) => prev.filter((p) => p.id !== projId));
      if (activeProjectId === projId) {
        const remaining = projects.filter((p) => p.id !== projId);
        if (remaining.length > 0) setActiveProjectId(remaining[0].id);
      }
    }
  };

  const toggleDocSelection = (docId) => {
    setSelectedDocs((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    );
  };

  return (
    <div className="projects-modal-backdrop" onClick={onClose}>
      <div className="projects-modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="projects-modal-header">
          <div className="projects-header-title">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
            </svg>
            <div>
              <h3>Workspace Projects</h3>
              <p>Organize your documents, chat threads, and grounded retrieval into dedicated workspaces</p>
            </div>
          </div>
          <button className="btn-close-projects" onClick={onClose} title="Close">
            ✕
          </button>
        </div>

        {/* Toolbar */}
        <div className="projects-toolbar">
          <button
            className={`btn-toggle-create-proj ${showCreateForm ? "active" : ""}`}
            onClick={() => setShowCreateForm(!showCreateForm)}
          >
            {showCreateForm ? "✕ Cancel" : "+ Create New Project"}
          </button>
          <span className="projects-count-info">{projects.length} workspaces configured</span>
        </div>

        {/* Create Project Form */}
        {showCreateForm && (
          <form onSubmit={handleCreate} className="create-project-card-form">
            <h4>New Project Workspace</h4>

            <div className="proj-form-field">
              <label>Project Title</label>
              <input
                type="text"
                required
                placeholder="e.g. Q3 Financial Audit or Clinical Research"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                autoFocus
              />
            </div>

            <div className="proj-form-field">
              <label>Description / Objective</label>
              <textarea
                rows={2}
                placeholder="Brief summary of research or document objectives..."
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
              />
            </div>

            {documents.length > 0 && (
              <div className="proj-form-field">
                <label>Assign Documents to Project</label>
                <div className="doc-selection-pills">
                  {documents.map((d) => {
                    const isSelected = selectedDocs.includes(d.id);
                    return (
                      <button
                        type="button"
                        key={d.id}
                        className={`doc-pill-select ${isSelected ? "selected" : ""}`}
                        onClick={() => toggleDocSelection(d.id)}
                      >
                        {isSelected ? "✓ " : "+ "}
                        {d.filename}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            <button type="submit" className="btn-submit-new-proj">
              Save & Launch Project
            </button>
          </form>
        )}

        {/* Projects Grid / List */}
        <div className="projects-grid-container">
          {projects.map((proj) => {
            const isActive = activeProjectId === proj.id;
            return (
              <div
                key={proj.id}
                className={`project-workspace-card ${isActive ? "active" : ""}`}
                onClick={() => {
                  setActiveProjectId(proj.id);
                }}
              >
                <div className="proj-card-top">
                  <div className="proj-folder-icon">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
                    </svg>
                  </div>
                  {isActive && <span className="active-proj-pill">● Active Workspace</span>}
                </div>

                <div className="proj-card-body">
                  <h4 className="proj-card-title">{proj.title}</h4>
                  <p className="proj-card-desc">{proj.description}</p>
                </div>

                <div className="proj-card-footer">
                  <span className="proj-stat-tag">
                    📄 {proj.doc_count || (proj.doc_ids ? proj.doc_ids.length : 1)} documents
                  </span>
                  <div className="proj-actions">
                    <button
                      className="btn-select-proj"
                      onClick={(e) => {
                        e.stopPropagation();
                        setActiveProjectId(proj.id);
                        onClose();
                      }}
                    >
                      {isActive ? "Active" : "Switch to Project"}
                    </button>
                    {projects.length > 1 && (
                      <button
                        className="btn-delete-proj"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(proj.id);
                        }}
                        title="Delete project"
                      >
                        ✕
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
