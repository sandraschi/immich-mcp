import { API_BASE } from "@/lib/api";
import { Code2, ExternalLink } from "lucide-react";
import { useState } from "react";

const QUICK_REFS = [
  "GET /api/v1/health",
  "GET /api/v1/photos/timeline",
  "GET /api/v1/albums",
  "GET /api/v1/people",
  "POST /api/v1/people/cleanup",
  "POST /api/v1/people/bulk-delete",
  "GET /api/v1/map/features",
  "GET /api/v1/libraries",
];

export function ApiDocs() {
  const [view, setView] = useState<"swagger" | "redoc">("swagger");
  const backend = API_BASE || "";
  const docsUrl = `${backend}/docs`;
  const redocUrl = `${backend}/redoc`;
  const openapiUrl = `${backend}/openapi.json`;

  return (
    <div className="space-y-6" data-testid="api-docs-page">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="mb-2 text-3xl font-bold tracking-tight text-white">API Docs</h1>
          <p className="text-slate-400">
            Auto-generated FastAPI reference (Swagger UI + ReDoc) for this server&apos;s REST API.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 rounded-lg border border-slate-800 bg-slate-900/50 p-1">
            <button
              type="button"
              onClick={() => setView("swagger")}
              data-testid="api-docs-view-swagger"
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-all ${view === "swagger" ? "bg-primary text-primary-foreground shadow-lg" : "text-slate-400 hover:text-white"}`}
            >
              Swagger
            </button>
            <button
              type="button"
              onClick={() => setView("redoc")}
              data-testid="api-docs-view-redoc"
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-all ${view === "redoc" ? "bg-primary text-primary-foreground shadow-lg" : "text-slate-400 hover:text-white"}`}
            >
              ReDoc
            </button>
          </div>
          <a
            href={view === "swagger" ? docsUrl : redocUrl}
            target="_blank"
            rel="noreferrer"
            data-testid="api-docs-open-browser"
            className="flex items-center gap-1 rounded-lg border border-slate-700 px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white"
          >
            <ExternalLink className="h-3 w-3" /> Open in browser
          </a>
        </div>
      </div>

      <div className="flex gap-2 overflow-x-auto pb-1" data-testid="api-docs-quick-ref">
        {QUICK_REFS.map((r) => (
          <code
            key={r}
            className="whitespace-nowrap rounded-md border border-slate-800 bg-slate-900/60 px-2 py-1 font-mono text-[11px] text-slate-300"
          >
            {r}
          </code>
        ))}
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-800/50 bg-slate-950/50 backdrop-blur-sm">
        <div className="flex items-center gap-2 border-b border-slate-800 px-4 py-2 text-xs text-slate-500">
          <Code2 className="h-3 w-3" />
          <span className="font-mono">{view === "swagger" ? docsUrl : redocUrl}</span>
          <span className="font-mono text-slate-600">· spec: {openapiUrl}</span>
        </div>
        <iframe
          title={view === "swagger" ? "Swagger UI" : "ReDoc"}
          src={view === "swagger" ? docsUrl : redocUrl}
          data-testid="api-docs-iframe"
          className="h-[70vh] w-full bg-[#09090b]"
        />
      </div>
    </div>
  );
}
