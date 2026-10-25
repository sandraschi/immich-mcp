import { useBackendStatus } from "@/common/backend-status";
import { cn } from "@/common/utils";
import {
  Bot,
  ChevronLeft,
  ChevronRight,
  Code2,
  Database,
  FolderOpen,
  GitCompareArrows,
  HelpCircle,
  Image,
  LayoutDashboard,
  Map as MapIcon,
  Settings,
  Terminal,
  Users,
  Wrench,
} from "lucide-react";
import { Link, useLocation } from "react-router-dom";

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const location = useLocation();
  const { state, health } = useBackendStatus();

  // SOTA order: domain pages first (Dashboard -> library), then platform
  // (Tools/Chat/Logs), then meta (API Docs/Help/Settings).
  const navItems = [
    { href: "/", label: "Dashboard", icon: LayoutDashboard, testid: "sidebar-nav-dashboard" },
    { href: "/photos", label: "Photos", icon: Image, testid: "sidebar-nav-photos" },
    { href: "/albums", label: "Albums", icon: FolderOpen, testid: "sidebar-nav-albums" },
    { href: "/people", label: "People", icon: Users, testid: "sidebar-nav-people" },
    { href: "/map", label: "Map View", icon: MapIcon, testid: "sidebar-nav-map" },
    { href: "/libraries", label: "Libraries", icon: Database, testid: "sidebar-nav-libraries" },
    {
      href: "/reconcile",
      label: "Reconcile",
      icon: GitCompareArrows,
      testid: "sidebar-nav-reconcile",
    },
    { href: "/tools", label: "Tools", icon: Wrench, testid: "sidebar-nav-tools" },
    { href: "/chat", label: "AI Chat", icon: Bot, testid: "sidebar-nav-chat" },
    { href: "/logger", label: "System Logs", icon: Terminal, testid: "sidebar-nav-logs" },
    { href: "/api-docs", label: "API Docs", icon: Code2, testid: "sidebar-nav-api-docs" },
    { href: "/help", label: "Help", icon: HelpCircle, testid: "sidebar-nav-help" },
    { href: "/settings", label: "Settings", icon: Settings, testid: "sidebar-nav-settings" },
  ];

  const isActive = (href: string) =>
    href === "/" ? location.pathname === "/" : location.pathname.startsWith(href);

  const dotColor =
    state === "online" ? "bg-emerald-500" : state === "connecting" ? "bg-amber-500" : "bg-red-500";
  const statusLabel =
    state === "online" ? "Online" : state === "connecting" ? "Connecting" : "Offline";

  return (
    <aside
      data-testid="sidebar"
      className={cn(
        "relative flex flex-col border-r border-slate-800 bg-slate-950/50 backdrop-blur-xl transition-all duration-300 ease-in-out",
        collapsed ? "w-16" : "w-64",
      )}
    >
      {/* Header: logo + version + collapse toggle (SOTA: toggle at TOP, not bottom) */}
      <div className="flex h-16 items-center justify-between border-b border-slate-800 px-4">
        <div className="flex min-w-0 items-center gap-2 font-semibold text-slate-100">
          <Image className="h-6 w-6 shrink-0 text-blue-500" />
          {!collapsed && (
            <span className="animate-in fade-in duration-300 truncate">
              Immich MCP
              {health?.version && (
                <span
                  data-testid="sidebar-version"
                  className="ml-2 rounded bg-slate-800 px-1.5 py-0.5 text-[10px] font-medium text-slate-400"
                >
                  v{health.version}
                </span>
              )}
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={onToggle}
          data-testid="sidebar-toggle"
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md p-1 text-slate-400 transition-colors hover:bg-slate-800 hover:text-white"
        >
          {collapsed ? <ChevronRight className="h-5 w-5" /> : <ChevronLeft className="h-5 w-5" />}
        </button>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto p-2">
        {navItems.map((item) => {
          const active = isActive(item.href);
          return (
            <Link
              key={item.href}
              to={item.href}
              data-testid={item.testid}
              className={cn(
                "group flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-slate-800 hover:text-white",
                active ? "bg-slate-800 text-white" : "text-slate-400",
                collapsed ? "justify-center" : "justify-start",
              )}
            >
              <item.icon
                className={cn("h-5 w-5 shrink-0", !collapsed && "mr-3", active && "text-blue-400")}
              />
              {!collapsed && <span className="truncate">{item.label}</span>}

              {/* Tooltip for collapsed mode */}
              {collapsed && (
                <div className="absolute left-full z-50 ml-2 hidden whitespace-nowrap rounded bg-slate-800 px-2 py-1 text-xs text-white group-hover:block">
                  {item.label}
                </div>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Connection status indicator (SOTA: always visible in sidebar) */}
      <div className="border-t border-slate-800 p-2" data-testid="sidebar-status">
        <div
          className={cn(
            "flex items-center rounded-md px-3 py-2 text-xs text-slate-400",
            collapsed ? "justify-center" : "justify-start gap-2",
          )}
          title={
            state === "online"
              ? `Backend online${health?.version ? ` v${health.version}` : ""}`
              : "Backend offline"
          }
        >
          <span className="relative flex h-2 w-2 shrink-0">
            {state === "connecting" && (
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75" />
            )}
            <span className={cn("relative inline-flex h-2 w-2 rounded-full", dotColor)} />
          </span>
          {!collapsed && (
            <span className="truncate">
              {statusLabel}
              {state === "online" && health?.version ? ` · v${health.version}` : ""}
            </span>
          )}
        </div>
      </div>
    </aside>
  );
}
