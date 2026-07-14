import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { API_BASE } from "@/lib/api";
import { Download, RefreshCcw, Terminal } from "lucide-react";
import { useEffect, useRef, useState } from "react";

export function Logger() {
  const [logs, setLogs] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/logs?limit=200`);
      const data = await res.json();
      if (data.success) {
        setLogs(data.logs);
      }
    } catch (err) {
      console.error("Failed to fetch logs", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white mb-2">System Logs</h2>
          <p className="text-slate-400">Monitor MCP server activity and Immich API interactions</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchLogs}
            disabled={loading}
            className="border-slate-800 bg-slate-900 text-slate-300"
          >
            <RefreshCcw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="border-slate-800 bg-slate-900 text-slate-300"
          >
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      <Card className="border-slate-800 bg-black/50 backdrop-blur-sm">
        <CardHeader className="border-b border-slate-800 pb-4">
          <div className="flex items-center gap-2">
            <Terminal className="h-5 w-5 text-emerald-500" />
            <CardTitle className="text-white text-lg">Server Output</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <ScrollArea className="h-[600px] w-full p-4 font-mono text-sm">
            <div ref={scrollRef} className="space-y-1">
              {logs.map((line, i) => {
                const isError =
                  line.toLowerCase().includes("error") || line.toLowerCase().includes("exception");
                const isWarning = line.toLowerCase().includes("warn");
                return (
                  <div key={i} className="flex gap-4 group">
                    <span className="text-slate-600 select-none w-12 text-right">{i + 1}</span>
                    <span
                      className={
                        isError ? "text-red-400" : isWarning ? "text-yellow-400" : "text-slate-300"
                      }
                    >
                      {line}
                    </span>
                  </div>
                );
              })}
              {logs.length === 0 && !loading && (
                <p className="text-slate-500 italic">No logs available.</p>
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
