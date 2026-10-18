/**
 * DocuChat AI - Production WebSocket Client
 * Provides resilient, low-latency streaming for:
 * 1. Interactive Chat (/ws/chat) with token streaming & citation delivery.
 * 2. Real-time document ingestion progress (/ws/documents/:id/progress).
 */

const WS_BASE = process.env.REACT_APP_WS_BASE || "ws://localhost:5000";

export class ChatWebSocketClient {
  constructor() {
    this.ws = null;
    this.handlers = {
      start: [],
      token: [],
      citations: [],
      complete: [],
      error: [],
      close: [],
    };
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 3;
    this.isConnected = false;
  }

  connect(token = null) {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    const url = token ? `${WS_BASE}/ws/chat?token=${encodeURIComponent(token)}` : `${WS_BASE}/ws/chat`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this.isConnected = true;
      this.reconnectAttempts = 0;
      console.log("[WS Chat] Connected successfully.");
    };

    this.ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        const eventType = payload.event;
        const listeners = this.handlers[eventType] || [];
        listeners.forEach((fn) => fn(payload.data, payload.request_id));
      } catch (e) {
        console.error("[WS Chat] Malformed message:", event.data);
      }
    };

    this.ws.onerror = (err) => {
      console.error("[WS Chat] Error:", err);
      (this.handlers.error || []).forEach((fn) => fn({ message: "WebSocket connection error" }));
    };

    this.ws.onclose = () => {
      this.isConnected = false;
      console.log("[WS Chat] Disconnected.");
      (this.handlers.close || []).forEach((fn) => fn());
    };
  }

  on(event, callback) {
    if (this.handlers[event]) {
      this.handlers[event].push(callback);
    }
    return () => {
      this.off(event, callback);
    };
  }

  off(event, callback) {
    if (this.handlers[event]) {
      this.handlers[event] = this.handlers[event].filter((fn) => fn !== callback);
    }
  }

  sendMessage(data) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      this.connect();
      // Retry send after slight delay
      setTimeout(() => {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
          this.ws.send(JSON.stringify(data));
        }
      }, 500);
      return;
    }
    this.ws.send(JSON.stringify(data));
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

/**
 * Subscribes to live ingestion job progress for a specific document.
 */
export function subscribeDocumentProgress(docId, onProgress, onComplete, onError) {
  const url = `${WS_BASE}/ws/documents/${docId}/progress`;
  const ws = new WebSocket(url);

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.ping) return;
      onProgress && onProgress(data);
      if (data.status === "ready" || data.status === "failed") {
        onComplete && onComplete(data);
        ws.close();
      }
    } catch (e) {
      console.error("[WS Progress] Parse error:", e);
    }
  };

  ws.onerror = (err) => {
    onError && onError(err);
  };

  return () => {
    if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
      ws.close();
    }
  };
}

export const chatWs = new ChatWebSocketClient();
