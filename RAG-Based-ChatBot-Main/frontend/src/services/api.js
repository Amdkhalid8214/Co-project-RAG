/**
 * DocuChat AI - Unified REST API Client
 * Manages JWT authorization headers, base URLs, error handling,
 * documents, conversations, and safe tool invocations.
 */

const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:5000/api";

function getAuthHeaders() {
  const token = localStorage.getItem("docuchat_token");
  const headers = { "Content-Type": "application/json" };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

export const api = {
  // Auth
  async login(username, password) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || err.message || "Login failed");
    }
    return res.json();
  },

  async register(username, password, email) {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password, email }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || err.message || "Registration failed");
    }
    return res.json();
  },

  async getMe() {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error("Unauthorized");
    return res.json();
  },

  async logout() {
    try {
      await fetch(`${API_BASE}/auth/logout`, {
        method: "POST",
        headers: getAuthHeaders(),
      });
    } catch {}
    localStorage.removeItem("docuchat_token");
    localStorage.removeItem("docuchat_user");
  },

  // Documents
  async listDocuments(skip = 0, limit = 50) {
    const res = await fetch(`${API_BASE}/documents?skip=${skip}&limit=${limit}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error("Failed to load documents");
    return res.json();
  },

  async uploadDocument(file) {
    const formData = new FormData();
    formData.append("file", file);
    const token = localStorage.getItem("docuchat_token");
    const headers = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const res = await fetch(`${API_BASE}/documents`, {
      method: "POST",
      headers,
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || err.message || "Upload failed");
    }
    return res.json();
  },

  async getDocumentStatus(docId) {
    const res = await fetch(`${API_BASE}/documents/${docId}/status`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error("Failed to fetch document status");
    return res.json();
  },

  async deleteDocument(docId) {
    const res = await fetch(`${API_BASE}/documents/${docId}`, {
      method: "DELETE",
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error("Failed to delete document");
    return res.json();
  },

  // Conversations
  async listConversations(skip = 0, limit = 50) {
    const res = await fetch(`${API_BASE}/conversations?skip=${skip}&limit=${limit}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error("Failed to load conversations");
    return res.json();
  },

  async createConversation(title = "New Chat") {
    const res = await fetch(`${API_BASE}/conversations`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ title }),
    });
    if (!res.ok) throw new Error("Failed to create conversation");
    return res.json();
  },

  async getConversation(convId) {
    const res = await fetch(`${API_BASE}/conversations/${convId}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error("Failed to fetch conversation");
    return res.json();
  },

  async deleteConversation(convId) {
    const res = await fetch(`${API_BASE}/conversations/${convId}`, {
      method: "DELETE",
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error("Failed to delete conversation");
    return res.json();
  },

  // Health
  async getHealth() {
    const res = await fetch(`http://localhost:5000/health`);
    return res.json();
  },

  async getReadiness() {
    const res = await fetch(`http://localhost:5000/ready`);
    return res.json();
  }
};
