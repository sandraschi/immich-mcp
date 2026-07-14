import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { API_BASE } from "@/lib/api";
import { useEffect, useState } from "react";

interface ImmichUser {
  name: string;
  role: string;
  description: string;
}

export function Settings() {
  const [users, setUsers] = useState<ImmichUser[]>([]);
  const [activeUser, setActiveUser] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/users`)
      .then((res) => res.json())
      .then((data) => {
        setUsers(data.users || []);
        setActiveUser(data.active_user);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to fetch users", err);
        setLoading(false);
      });
  }, []);

  const switchUser = async (username: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/users/active`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username }),
      });
      const data = await res.json();
      if (data.success) {
        setActiveUser(data.active_user);
      }
    } catch (err) {
      console.error("Failed to switch user", err);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white mb-2">Settings</h2>
        <p className="text-slate-400">Manage connections and preferences</p>
      </div>

      <div className="grid gap-6">
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-white">Immich Multi-User Accounts</CardTitle>
            <CardDescription className="text-slate-400">
              Select the active user context for the MCP Server
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {loading ? (
              <p className="text-slate-400">Loading accounts...</p>
            ) : users.length > 0 ? (
              <div className="space-y-3">
                {users.map((user) => (
                  <div
                    key={user.name}
                    className={`p-3 rounded-md border flex items-center justify-between ${
                      activeUser === user.name
                        ? "border-indigo-500 bg-indigo-500/10"
                        : "border-slate-800 bg-slate-900"
                    }`}
                  >
                    <div>
                      <p className="text-slate-200 font-medium">
                        {user.name}{" "}
                        {activeUser === user.name && (
                          <span className="text-indigo-400 text-xs ml-2">(Active)</span>
                        )}
                      </p>
                      <p className="text-slate-500 text-sm">
                        Role: {user.role} {user.description && `| ${user.description}`}
                      </p>
                    </div>
                    {activeUser !== user.name && (
                      <button
                        onClick={() => switchUser(user.name)}
                        className="px-3 py-1.5 rounded-md text-xs font-medium border border-slate-750 text-slate-300 hover:bg-slate-800 transition-colors"
                      >
                        Switch to {user.name}
                      </button>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4 border border-slate-800 rounded-md bg-slate-900">
                <p className="text-slate-400">
                  No users configured. Please set the{" "}
                  <code className="text-slate-300 px-1">IMMICH_USERS</code> environment variable.
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-white">Local LLM Configuration</CardTitle>
            <CardDescription className="text-slate-400">
              Provider and model selection
            </CardDescription>
          </CardHeader>
          <CardContent>
            <LLMSettings />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function LLMSettings() {
  const [providers, setProviders] = useState<Record<string, { name: string }[]>>({});
  const [selectedProvider, setSelectedProvider] = useState("ollama");
  const [selectedModel, setSelectedModel] = useState("");
  useEffect(() => {
    fetch(`${API_BASE}/api/v1/llm/providers`)
      .then((r) => r.json())
      .then((d) => {
        setProviders(d);
        const savedP = localStorage.getItem("llm_provider") || "ollama";
        const savedM = localStorage.getItem("llm_model") || "";
        setSelectedProvider(savedP);
        const models = d[savedP === "ollama" ? "ollama" : "lm_studio"] || [];
        setSelectedModel(
          savedM && models.some((m: { name: string }) => m.name === savedM)
            ? savedM
            : models[0]?.name || "",
        );
      })
      .catch(() => {
        setProviders({ ollama: [{ name: "llama3.2:3b" }] });
        setSelectedModel(localStorage.getItem("llm_model") || "llama3.2:3b");
      });
  }, []);
  const save = (p: string, m: string) => {
    localStorage.setItem("llm_provider", p);
    localStorage.setItem("llm_model", m);
  };
  const models = providers[selectedProvider === "ollama" ? "ollama" : "lm_studio"] || [];
  return (
    <div className="space-y-3">
      <select
        className="h-9 w-full rounded-md border border-slate-700 bg-slate-900 px-3 text-sm text-slate-200"
        value={selectedProvider}
        onChange={(e) => {
          setSelectedProvider(e.target.value);
          save(e.target.value, "");
        }}
      >
        <option value="ollama">Ollama</option>
        <option value="lm_studio">LM Studio</option>
      </select>
      <select
        className="h-9 w-full rounded-md border border-slate-700 bg-slate-900 px-3 text-sm text-slate-200"
        value={selectedModel}
        onChange={(e) => {
          setSelectedModel(e.target.value);
          save(selectedProvider, e.target.value);
        }}
      >
        {models.map((m) => (
          <option key={m.name} value={m.name}>
            {m.name}
          </option>
        ))}
      </select>
    </div>
  );
}
