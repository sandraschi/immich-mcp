import { useState, useEffect } from 'react';
import { Loader2, Wrench, Code2, AlertCircle } from 'lucide-react';

interface Tool {
    name: string;
    description: string;
    parameters: Record<string, unknown>;
}

export function Tools() {
    const [tools, setTools] = useState<Tool[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchTools = async () => {
            try {
                const res = await fetch('/api/v1/tools');
                if (!res.ok) throw new Error('Failed to fetch tools');
                const data = await res.json();
                if (data.success) {
                    setTools(data.tools);
                } else {
                    throw new Error(data.message || 'Error loading tools');
                }
            } catch (err: unknown) {
                const errorMessage = err instanceof Error ? err.message : 'An error occurred';
                setError(errorMessage);
            } finally {
                setLoading(false);
            }
        };

        fetchTools();
    }, []);

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white mb-2">MCP Tools</h1>
                    <p className="text-slate-400">Explore the available Immich MCP tools and portmanteau structures.</p>
                </div>
            </div>

            <div className="bg-slate-950/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm min-h-[400px]">
                {loading && (
                    <div className="flex items-center justify-center h-48">
                        <Loader2 className="h-8 w-8 animate-spin text-primary" />
                    </div>
                )}

                {error && (
                    <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 mb-6 flex items-center gap-2">
                        <AlertCircle className="h-5 w-5" />
                        <span>{error}</span>
                    </div>
                )}

                {!loading && tools.length === 0 && !error && (
                    <div className="flex flex-col items-center justify-center h-full text-slate-500 py-12">
                        <Wrench className="h-12 w-12 mb-4 opacity-50" />
                        <p>No tools found.</p>
                    </div>
                )}

                {tools.length > 0 && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                        {tools.map(tool => (
                            <div key={tool.name} className="group relative p-5 bg-slate-900/80 hover:bg-slate-800 rounded-xl border border-slate-700/50 transition-all flex flex-col h-full">
                                <div className="flex items-center gap-3 mb-4">
                                    <div className="h-10 w-10 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 shrink-0">
                                        <Wrench className="h-5 w-5" />
                                    </div>
                                    <h3 className="text-lg font-semibold text-white break-all">{tool.name}</h3>
                                </div>

                                <p className="text-sm text-slate-400 mb-4 flex-grow">{tool.description}</p>

                                {tool.parameters && Object.keys(tool.parameters).length > 0 && (
                                    <div className="mt-auto bg-slate-950/80 rounded-lg border border-slate-800 p-3">
                                        <div className="flex items-center gap-2 mb-2 text-xs font-semibold text-slate-300 uppercase tracking-wider">
                                            <Code2 className="h-3 w-3" /> Parameters
                                        </div>
                                        <div className="text-xs text-slate-500 font-mono whitespace-pre-wrap break-all max-h-32 overflow-y-auto custom-scrollbar">
                                            {JSON.stringify(tool.parameters, null, 2)}
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
