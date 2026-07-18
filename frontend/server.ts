import express from "express";
import path from "path";
import { createServer as createViteServer } from "vite";
import { GoogleGenAI, Type } from "@google/genai";
import dotenv from "dotenv";

dotenv.config();

const app = express();
const PORT = 3000;

app.use(express.json());

// Initialize Gemini safely
let ai: GoogleGenAI | null = null;
const apiKey = process.env.GEMINI_API_KEY;

if (apiKey && apiKey !== "MY_GEMINI_API_KEY") {
  try {
    ai = new GoogleGenAI({
      apiKey: apiKey,
      httpOptions: {
        headers: {
          "User-Agent": "aistudio-build",
        },
      },
    });
    console.log("Gemini client successfully initialized.");
  } catch (error) {
    console.error("Failed to initialize Gemini client:", error);
  }
} else {
  console.log("No valid GEMINI_API_KEY found, running chat in fallback/simulation mode.");
}

// API: AI Chat - Proxy sang Backend /api/v1/ai/threads/{thread_id}/messages
// Backend trả về { ai_response: { content, citations }, extracted_logs }
// App.tsx mong đợi { text, extraction, citations }
app.post("/api/chat", async (req, res) => {
  const { messages, babyProfile } = req.body;

  if (!messages || !Array.isArray(messages)) {
    return res.status(400).json({ error: "Messages array is required" });
  }

  const userMessage = messages[messages.length - 1]?.content || "";

  // Sử dụng thread_id cố định cho session (hoặc lấy từ request nếu có)
  const threadId = req.body.thread_id || "default-thread";

  try {
    const backendUrl = `http://127.0.0.1:8000/api/v1/ai/threads/${threadId}/messages`;
    const response = await fetch(backendUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer mock-token",
      },
      body: JSON.stringify({
        content: userMessage,
        type: "text",
      }),
    });

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`);
    }

    const data = await response.json();

    // Chuyển đổi từ Backend format sang App.tsx format
    const aiContent = data.ai_response?.content || "Tôi đã ghi nhận thông tin đó!";
    const citations = data.ai_response?.citations || [];
    const extractedLogs = data.extracted_logs || [];

    // Chuyển extracted_log đầu tiên thành extraction widget nếu có
    let extraction = null;
    if (extractedLogs.length > 0) {
      const log = extractedLogs[0];
      extraction = {
        type: log.type,
        title: log.title,
        detail: log.detail,
        value: log.value,
        time: log.time,
        pending: false,
      };
    }

    return res.json({
      text: aiContent,
      extraction,
      citations,
    });
  } catch (error) {
    console.error("Backend AI chat error:", error);

    // Fallback nhẹ nếu backend không khởi động
    return res.json({
      text: "Xin lỗi, tôi đang gặp sự cố kết nối với máy chủ AI. Vui lòng thử lại sau.",
      extraction: null,
      citations: [],
    });
  }
});



// Proxy all other /api/v1/* requests to FastAPI backend
app.all("/api/v1/*", async (req, res) => {
  const targetUrl = `http://127.0.0.1:8000${req.originalUrl}`;
  try {
    const headers: Record<string, string> = {};
    for (const [key, val] of Object.entries(req.headers)) {
      if (typeof val === "string") {
        headers[key] = val;
      }
    }
    
    // Inject mock token if not present to bypass auth in dev environment
    if (!headers["authorization"]) {
      headers["authorization"] = "Bearer mock-token";
    }

    const response = await fetch(targetUrl, {
      method: req.method,
      headers: headers,
      body: ["POST", "PUT", "PATCH"].includes(req.method) ? JSON.stringify(req.body) : undefined,
    });

    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      const data = await response.json();
      res.status(response.status).json(data);
    } else {
      const text = await response.text();
      res.status(response.status).send(text);
    }
  } catch (error) {
    console.error(`Error proxying to backend:`, error);
    res.status(500).json({ error: "Failed to connect to backend service" });
  }
});

// Proxy /static/* requests to FastAPI backend (so static assets like baby photos work)
app.all("/static/*", async (req, res) => {
  const targetUrl = `http://127.0.0.1:8000${req.originalUrl}`;
  try {
    const response = await fetch(targetUrl, {
      method: req.method,
    });

    const contentType = response.headers.get("content-type");
    if (contentType) {
      res.setHeader("content-type", contentType);
    }

    const buffer = await response.arrayBuffer();
    res.status(response.status).send(Buffer.from(buffer));
  } catch (error) {
    console.error(`Error proxying static asset to backend:`, error);
    res.status(500).json({ error: "Failed to connect to backend service" });
  }
});

// Setup Vite middleware or static serving
const startServer = async () => {
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
    console.log("Vite development server middleware loaded.");
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
    console.log("Serving static files in production mode.");
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Express server running on http://0.0.0.0:${PORT}`);
  });
};

startServer();
