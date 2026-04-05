import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

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
        fetch("/api/v1/users")
            .then(res => res.json())
            .then(data => {
                setUsers(data.users || []);
                setActiveUser(data.active_user);
                setLoading(false);
            })
            .catch(err => {
                console.error("Failed to fetch users", err);
                setLoading(false);
            });
    }, []);

    const switchUser = async (username: string) => {
        try {
            const res = await fetch("/api/v1/users/active", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username })
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
                        <CardDescription className="text-slate-400">Select the active user context for the MCP Server</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {loading ? (
                            <p className="text-slate-400">Loading accounts...</p>
                        ) : users.length > 0 ? (
                            <div className="space-y-3">
                                {users.map((user) => (
                                    <div
                                        key={user.name}
                                        className={`p-3 rounded-md border flex items-center justify-between ${activeUser === user.name
                                                ? 'border-indigo-500 bg-indigo-500/10'
                                                : 'border-slate-800 bg-slate-900'
                                            }`}
                                    >
                                        <div>
                                            <p className="text-slate-200 font-medium">
                                                {user.name} {activeUser === user.name && <span className="text-indigo-400 text-xs ml-2">(Active)</span>}
                                            </p>
                                            <p className="text-slate-500 text-sm">Role: {user.role} {user.description && `| ${user.description}`}</p>
                                        </div>
                                        {activeUser !== user.name && (
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => switchUser(user.name)}
                                                className="border-slate-700 text-slate-300 hover:bg-slate-800"
                                            >
                                                Switch to {user.name}
                                            </Button>
                                        )}
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="p-4 border border-slate-800 rounded-md bg-slate-900">
                                <p className="text-slate-400">No users configured. Please set the <code className="text-slate-300 px-1">IMMICH_USERS</code> environment variable.</p>
                            </div>
                        )}
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="text-white">Local LLM Configuration</CardTitle>
                        <CardDescription className="text-slate-400">Settings for local inference (e.g., Ollama)</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid gap-2">
                            <Label className="text-slate-300">Ollama API URL</Label>
                            <Input
                                className="bg-slate-900 border-slate-800 text-slate-100 placeholder:text-slate-400"
                                placeholder="http://localhost:11434"
                                defaultValue="http://localhost:11434"
                            />
                        </div>
                        <div className="grid gap-2">
                            <Label className="text-slate-300">Local Model</Label>
                            <Input
                                className="bg-slate-900 border-slate-800 text-slate-100 placeholder:text-slate-400"
                                defaultValue="llama3.3"
                            />
                        </div>
                        <div className="pt-2">
                            <Button variant="outline" className="border-slate-800 text-slate-300 hover:bg-slate-800">
                                Save Local AI Settings
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
