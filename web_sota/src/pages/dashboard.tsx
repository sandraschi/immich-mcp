import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, Image, Zap, Cpu, HardDrive, Loader2 } from "lucide-react";

interface StorageInfo {
    used_bytes: number;
    available_bytes: number;
    total_bytes: number;
    usage_percentage: number;
    photo_count: number;
    video_count: number;
    user_count: number;
    album_count: number;
}

interface ServerHealth {
    server_version: string;
    server_features: string[];
    is_v2_plus: boolean;
    database_connected: boolean;
    redis_connected: boolean;
    uptime_seconds: number;
    response_time_ms: number;
}

export function Dashboard() {
    const [storage, setStorage] = useState<StorageInfo | null>(null);
    const [health, setHealth] = useState<ServerHealth | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchDashboardData = async () => {
            try {
                const [storageRes, healthRes] = await Promise.all([
                    fetch('/api/v1/system/storage'),
                    fetch('/api/v1/system/health')
                ]);

                if (!storageRes.ok) {
                    const body = await storageRes.json().catch(() => ({}));
                    const msg = (body as { detail?: string }).detail || storageRes.statusText || 'Failed to fetch storage';
                    throw new Error(msg);
                }
                if (!healthRes.ok) {
                    const body = await healthRes.json().catch(() => ({}));
                    const msg = (body as { detail?: string }).detail || healthRes.statusText || 'Failed to fetch health';
                    throw new Error(msg);
                }

                const storageData = await storageRes.json();
                const healthData = await healthRes.json();

                setStorage(storageData);
                setHealth(healthData);
            } catch (err: unknown) {
                const errorMessage = err instanceof Error ? err.message : 'Error loading dashboard';
                setError(errorMessage);
            } finally {
                setLoading(false);
            }
        };

        fetchDashboardData();
    }, []);

    const formatBytes = (bytes: number) => {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="space-y-6">
                <h2 className="text-2xl font-bold tracking-tight text-white">Immich Dashboard</h2>
                <div className="p-6 bg-red-500/10 border border-red-500/30 rounded-xl text-red-300 space-y-2">
                    <p className="font-medium">Connection error</p>
                    <p className="text-sm">{error}</p>
                    <p className="text-xs text-slate-400 mt-2">Fix .env (IMMICH_SERVER_URL, IMMICH_API_KEY) and restart the backend.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">Immich Dashboard</h2>
                    <p className="text-slate-400">Photo library and synchronization status</p>
                </div>
            </div>

            {/* KPI Cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-200">
                            Total Assets
                        </CardTitle>
                        <Image className="h-4 w-4 text-emerald-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">
                            {(storage?.photo_count || 0) + (storage?.video_count || 0)}
                        </div>
                        <p className="text-xs text-slate-400">
                            Photos: {storage?.photo_count || 0} • Videos: {storage?.video_count || 0}
                        </p>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-200">
                            Library Size
                        </CardTitle>
                        <HardDrive className="h-4 w-4 text-blue-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">
                            {formatBytes(storage?.used_bytes || 0)}
                        </div>
                        <p className="text-xs text-slate-400">
                            {storage?.usage_percentage.toFixed(1) || 0}% used of {formatBytes(storage?.total_bytes || 0)}
                        </p>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-200">
                            System Health
                        </CardTitle>
                        <Cpu className="h-4 w-4 text-purple-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">
                            {health?.database_connected && health?.redis_connected ? 'Healthy' : 'Degraded'}
                        </div>
                        <p className="text-xs text-slate-400">
                            Version {health?.server_version || 'Unknown'}
                        </p>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-200">
                            API Bridge
                        </CardTitle>
                        <Zap className="h-4 w-4 text-orange-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">{health?.response_time_ms || 0} ms</div>
                        <p className="text-xs text-slate-400">
                            Avg Response Time
                        </p>
                    </CardContent>
                </Card>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                <Card className="col-span-4 border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="text-white">Quick Status</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4 font-medium text-sm text-slate-300">
                            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                                <span>Platform Version</span>
                                <span className="text-primary">{health?.server_version}</span>
                            </div>
                            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                                <span>Database Status</span>
                                <span className={health?.database_connected ? 'text-emerald-500' : 'text-red-500'}>
                                    {health?.database_connected ? 'Connected' : 'Disconnected'}
                                </span>
                            </div>
                            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                                <span>Redis Cache</span>
                                <span className={health?.redis_connected ? 'text-emerald-500' : 'text-red-500'}>
                                    {health?.redis_connected ? 'Connected' : 'Disconnected'}
                                </span>
                            </div>
                            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                                <span>Registered Users</span>
                                <span>{storage?.user_count}</span>
                            </div>
                            <div className="flex items-center justify-between pb-2">
                                <span>Total Albums</span>
                                <span>{storage?.album_count}</span>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card className="col-span-3 border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="text-white">Active Features</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {health?.server_features?.slice(0, 4).map((feature: string) => (
                                <div key={feature} className="flex items-center">
                                    <Activity className="h-4 w-4 text-emerald-500 mr-2" />
                                    <div className="ml-2 space-y-1">
                                        <p className="text-sm font-medium leading-none text-white capitalize">{feature.replace(/_/g, ' ')}</p>
                                        <p className="text-xs text-slate-400">System capability enabled</p>
                                    </div>
                                </div>
                            ))}
                            {(!health?.server_features || health.server_features.length === 0) && (
                                <div className="text-sm text-slate-500 italic">No features listed</div>
                            )}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
