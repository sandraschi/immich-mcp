import { API_BASE } from "@/lib/api";
import { Bot, Cpu, Download, Eraser, Layers, Loader2, Send, Sparkles, User } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

const HISTORY_KEY = "immich-chat-history";
const PERSONALITY_KEY = "immich-chat-personality";
const MAX_HISTORY = 100;

const PERSONALITIES: Record<string, string> = {
  "Photo Curator":
    "You are an Immich photo curation expert. Help organize, tag, and manage photo libraries. Provide guidance on albums, metadata editing, and photo organization.",
  "Album Manager":
    "You are an album management specialist. Focus on creating, organizing, and sharing photo albums. Provide tips on album structure and collaborative features.",
  "Quick Summarizer": "Keep responses to 2-3 sentences. Focus on key facts.",
  Custom: "Custom prompt \u2014 editable below.",
};

const EXAMPLE_PROMPTS = [
  {
    group: "Photos",
    prompts: ["Find photos from last week", "Show recent uploads", "Search for photos with people"],
  },
  {
    group: "Albums",
    prompts: ["Create a new album", "Add photos to album Travel 2024", "List all shared albums"],
  },
  {
    group: "Search",
    prompts: ["Search for sunset photos", "Find photos by location", "Search by date range"],
  },
];

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  provider?: string;
  model?: string;
}
interface LLMProvider {
  id: string;
  name: string;
  url: string;
}

export function Chat() {
  const [personality, setPersonality] = useState(
    () => localStorage.getItem(PERSONALITY_KEY) || "Photo Curator",
  );
  const [messages, setMessages] = useState<Message[]>(() => {
    try {
      return JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
    } catch {
      return [];
    }
  });
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [providers, setProviders] = useState<LLMProvider[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>("ollama");
  const [models, setModels] = useState<string[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(messages));
  }, [messages]);
  useEffect(() => {
    localStorage.setItem(PERSONALITY_KEY, personality);
  }, [personality]);
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/llm/providers`)
      .then((res) => res.json())
      .then((data) => {
        if (data.success) setProviders(data.providers);
      });
  }, []);

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/llm/models?provider=${selectedProvider}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          setModels(data.models);
          if (data.models.length > 0) setSelectedModel(data.models[0]);
        }
      });
  }, [selectedProvider]);

  useEffect(() => {
    if (messages.length === 0) {
      setMessages([
        {
          role: "assistant",
          content:
            "Hello! I'm your Immich AI assistant. How can I help you with your photo library today?",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSend = useCallback(async () => {
    if (!input.trim() || loading) return;
    const userMsg: Message = {
      role: "user",
      content: input,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };
    setMessages((prev) => {
      const next = [...prev, userMsg];
      return next.length > MAX_HISTORY ? next.slice(-MAX_HISTORY) : next;
    });
    setInput("");
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: input,
          provider: selectedProvider,
          model: selectedModel,
          personality,
        }),
      });
      const data = await res.json();
      if (data.success) {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: data.response,
            timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
            provider: selectedProvider,
            model: selectedModel,
          },
        ]);
      }
    } catch (err) {
      console.error("Chat error", err);
    } finally {
      setLoading(false);
    }
  }, [input, loading, selectedProvider, selectedModel, personality]);

  const exportChat = () => {
    const text = messages
      .map((m) => `[${m.timestamp}] [${m.role.toUpperCase()}] ${m.content}`)
      .join("\n\n");
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "immich-chat.txt";
    a.click();
    URL.revokeObjectURL(url);
  };

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <div data-testid="chat-page" className="flex h-[calc(100vh-8rem)] flex-col space-y-4">
      <div
        data-testid="chat-controls"
        className="flex items-center justify-between flex-wrap gap-2"
      >
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-indigo-400" />
            Immich AI Assistant
          </h2>
          <p className="text-slate-400">Natural language photo management and search</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500 bg-slate-800 px-2 py-1 rounded">
            skill:immich-expert
          </span>
          <div className="relative">
            <select
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value)}
              className="appearance-none bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200 pr-6"
            >
              {providers.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
            <Layers className="h-3 w-3 text-indigo-400 absolute right-1.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>
          <div className="relative">
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="appearance-none bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200 pr-6"
            >
              {models.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
            <Cpu className="h-3 w-3 text-emerald-400 absolute right-1.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>
          <select
            data-testid="personality-select"
            className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200"
            value={personality}
            onChange={(e) => setPersonality(e.target.value)}
          >
            {Object.keys(PERSONALITIES).map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
          <button
            data-testid="chat-export"
            onClick={exportChat}
            disabled={messages.length === 0}
            className="p-1.5 rounded hover:bg-slate-800 text-slate-400 disabled:opacity-30"
            title="Export"
          >
            <Download className="h-4 w-4" />
          </button>
          <button
            data-testid="chat-clear"
            onClick={clearChat}
            disabled={messages.length === 0}
            className="p-1.5 rounded hover:bg-slate-800 text-slate-400 disabled:opacity-30"
            title="Clear"
          >
            <Eraser className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-6">
        <div className="space-y-6">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex gap-4 ${msg.role === "assistant" ? "" : "flex-row-reverse"}`}
            >
              <div
                className={`h-10 w-10 rounded-full flex items-center justify-center border shrink-0 ${msg.role === "assistant" ? "bg-indigo-900/20 border-indigo-500/30" : "bg-slate-800 border-slate-700"}`}
              >
                {msg.role === "assistant" ? (
                  <Bot className="h-5 w-5 text-indigo-400" />
                ) : (
                  <User className="h-5 w-5 text-slate-400" />
                )}
              </div>
              <div
                className={`flex flex-col space-y-1 max-w-[80%] ${msg.role === "assistant" ? "" : "items-end"}`}
              >
                <div className="flex items-center gap-2 px-1">
                  <span className="text-xs font-medium text-slate-400">
                    {msg.role === "assistant" ? "Immich AI" : "Operator"}
                  </span>
                  <span className="text-[10px] text-slate-600">{msg.timestamp}</span>
                </div>
                <div
                  className={`text-sm p-4 rounded-2xl border ${msg.role === "assistant" ? "bg-slate-900/50 border-slate-800 text-slate-200 rounded-tl-none" : "bg-indigo-600 border-indigo-500 text-white rounded-tr-none"}`}
                >
                  {msg.content}
                  {msg.provider && (
                    <div className="mt-2 pt-2 border-t border-slate-800 flex items-center gap-2 text-[10px] text-slate-500">
                      <Cpu className="h-3 w-3" />
                      <span>
                        Inference: {msg.provider} / {msg.model}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex gap-4 animate-pulse">
              <div className="h-10 w-10 rounded-full bg-indigo-900/20 border border-indigo-500/30 flex items-center justify-center">
                <Loader2 className="h-5 w-5 text-indigo-400 animate-spin" />
              </div>
              <div className="space-y-2 flex-1">
                <div className="h-4 bg-slate-800 rounded w-1/4" />
                <div className="h-16 bg-slate-900/50 rounded-2xl w-1/2" />
              </div>
            </div>
          )}
        </div>
        <div ref={scrollRef} />
      </div>

      <div data-testid="example-prompts" className="flex flex-wrap gap-2">
        {EXAMPLE_PROMPTS.map((group) => (
          <div key={group.group} className="flex flex-wrap items-center gap-1">
            <span className="text-xs text-slate-500 mr-1">{group.group}:</span>
            {group.prompts.map((p) => (
              <button
                key={p}
                onClick={() => setInput(p)}
                className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-2 py-1 rounded"
              >
                {p}
              </button>
            ))}
          </div>
        ))}
      </div>

      <div className="p-4 border-t border-slate-800 bg-slate-900/50">
        <div className="flex gap-2 max-w-4xl mx-auto">
          <textarea
            data-testid="chat-input"
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 resize-none transition-all"
            placeholder="Ask Immich AI to find photos, create albums, or analyze people..."
          />
          <button
            data-testid="chat-send"
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-xl px-6 h-auto"
          >
            {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
          </button>
        </div>
      </div>
    </div>
  );
}
