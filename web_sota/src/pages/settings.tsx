import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { API_BASE } from "@/lib/api";
import { useLlmStore } from "@/store/llm";
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

interface LlmProvider {
  id: string;
  name: string;
  url: string;
}

function LLMSettings() {
  const [providers, setProviders] = useState<LlmProvider[]>([]);
  const [models, setModels] = useState<string[]>([]);
  const [modelsError, setModelsError] = useState<string | null>(null);
  const [loadingModels, setLoadingModels] = useState(false);
  const selectedProvider = useLlmStore((s) => s.selectedProvider);
  const selectedModel = useLlmStore((s) => s.selectedModel);
  const setProvider = useLlmStore((s) => s.setProvider);
  const setModel = useLlmStore((s) => s.setModel);

  const fetchModels = (providerId: string) => {
    setLoadingModels(true);
    setModelsError(null);
    fetch(`${API_BASE}/api/v1/llm/models?provider=${encodeURIComponent(providerId)}`)
      .then((r) => r.json())
      .then((d) => {
        if (d.success && Array.isArray(d.models)) {
          setModels(d.models);
          const savedM = useLlmStore.getState().selectedModel;
          setModel(savedM && d.models.includes(savedM) ? savedM : (d.models[0] ?? ""));
        } else {
          setModels([]);
          setModelsError(d.error || "Could not load models");
        }
      })
      .catch(() => {
        setModels([]);
        setModelsError("Could not reach the backend");
      })
      .finally(() => setLoadingModels(false));
  };

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/llm/providers`)
      .then((r) => r.json())
      .then((d) => {
        const list: LlmProvider[] = Array.isArray(d.providers) ? d.providers : [];
        setProviders(list);
        const savedP = useLlmStore.getState().selectedProvider;
        const firstId = list[0]?.id ?? "ollama";
        const providerId = savedP && list.some((p) => p.id === savedP) ? savedP : firstId;
        setProvider(providerId);
        fetchModels(providerId);
      })
      .catch(() => setModelsError("Could not reach the backend"));
  }, []);

  const save = (p: string, m: string) => {
    setProvider(p);
    setModel(m);
  };

  return (
    <div className="space-y-3" data-testid="settings-page">
      <select
        data-testid="llm-provider-select"
        className="h-9 w-full rounded-md border border-slate-700 bg-slate-900 px-3 text-sm text-slate-200"
        value={selectedProvider}
        onChange={(e) => {
          const p = e.target.value;
          setProvider(p);
          save(p, "");
          fetchModels(p);
        }}
      >
        {providers.length === 0 && <option value="ollama">Ollama</option>}
        {providers.map((p) => (
          <option key={p.id} value={p.id}>
            {p.name}
          </option>
        ))}
      </select>
      <select
        data-testid="llm-model-select"
        className="h-9 w-full rounded-md border border-slate-700 bg-slate-900 px-3 text-sm text-slate-200"
        value={selectedModel}
        onChange={(e) => {
          setModel(e.target.value);
          save(selectedProvider, e.target.value);
        }}
        disabled={loadingModels || models.length === 0}
      >
        {loadingModels && <option value="">Loading models...</option>}
        {!loadingModels && models.length === 0 && (
          <option value="">{modelsError || "No models available"}</option>
        )}
        {models.map((m) => (
          <option key={m} value={m}>
            {m}
          </option>
        ))}
      </select>
      {modelsError && <p className="text-xs text-amber-400">{modelsError}</p>}
      {models.length > 0 && !modelsError && (
        <p className="text-xs text-slate-500">{models.length} model(s) detected</p>
      )}
    </div>
  );
}
