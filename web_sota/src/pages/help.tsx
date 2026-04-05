import { useState, useEffect } from 'react';
import { Loader2, HelpCircle, AlertCircle, BookOpen } from 'lucide-react';

interface HelpData {
    success: boolean;
    message?: string;
    categories?: string[];
    all_help?: Record<string, string>;
    category?: string;
    help?: string;
}

export function Help() {
    const [helpData, setHelpData] = useState<HelpData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchHelp = async () => {
            try {
                const res = await fetch('/api/v1/help');
                if (!res.ok) throw new Error('Failed to fetch help information');
                const data = await res.json();
                if (data.success) {
                    setHelpData(data);
                } else {
                    throw new Error(data.message || 'Error loading help');
                }
            } catch (err: unknown) {
                const errorMessage = err instanceof Error ? err.message : 'An error occurred';
                setError(errorMessage);
            } finally {
                setLoading(false);
            }
        };

        fetchHelp();
    }, []);

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white mb-2">System Help</h1>
                    <p className="text-slate-400">Documentation and usage guide for Immich MCP Server.</p>
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

                {!loading && !error && helpData && (
                    <div className="space-y-8">
                        <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
                            <div className="h-10 w-10 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                                <HelpCircle className="h-5 w-5" />
                            </div>
                            <h2 className="text-xl font-semibold text-white">{helpData.message || 'Help Categories'}</h2>
                        </div>

                        {helpData.all_help && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                {Object.entries(helpData.all_help).map(([category, details]) => (
                                    <div key={category} className="bg-slate-900/50 rounded-xl border border-slate-800 p-5 hover:border-slate-700 transition-colors">
                                        <div className="flex items-center gap-2 mb-3">
                                            <BookOpen className="h-4 w-4 text-emerald-400" />
                                            <h3 className="text-lg font-medium text-white capitalize">{category}</h3>
                                        </div>
                                        <p className="text-sm text-slate-400 leading-relaxed">
                                            {details}
                                        </p>
                                    </div>
                                ))}
                            </div>
                        )}

                        {!helpData.all_help && helpData.help && (
                            <div className="bg-slate-900/50 rounded-xl border border-slate-800 p-5">
                                <h3 className="text-lg font-medium text-white capitalize mb-4">{helpData.category} Help</h3>
                                <p className="text-slate-300">{helpData.help}</p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
