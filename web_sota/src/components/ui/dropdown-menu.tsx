import { cn } from "@/common/utils";
import * as React from "react";

const DropdownMenu = ({ children }: { children: React.ReactNode }) => {
  const [open, setOpen] = React.useState(false);
  const containerRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="relative inline-block text-left" ref={containerRef}>
      {React.Children.map(children, (child) => {
        if (React.isValidElement(child)) {
          // @ts-ignore
          if (child.type.displayName === "DropdownMenuTrigger") {
            return React.cloneElement(child, {
              // @ts-ignore
              onClick: () => setOpen(!open),
            });
          }
          // @ts-ignore
          if (child.type.displayName === "DropdownMenuContent") {
            return open ? child : null;
          }
        }
        return child;
      })}
    </div>
  );
};

const DropdownMenuTrigger = React.forwardRef<
  HTMLDivElement,
  { children: React.ReactNode; asChild?: boolean; onClick?: () => void }
>(({ children, onClick }, ref) => {
  return (
    <div ref={ref} onClick={onClick}>
      {children}
    </div>
  );
});
DropdownMenuTrigger.displayName = "DropdownMenuTrigger";

const DropdownMenuContent = ({
  children,
  className,
}: { children: React.ReactNode; className?: string }) => {
  return (
    <div
      className={cn(
        "absolute right-0 z-50 mt-2 w-56 origin-top-right rounded-md border border-slate-800 bg-slate-900 p-1 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none animate-in fade-in zoom-in-95 duration-100",
        className,
      )}
    >
      {children}
    </div>
  );
};
DropdownMenuContent.displayName = "DropdownMenuContent";

const DropdownMenuItem = ({
  children,
  onClick,
  className,
}: { children: React.ReactNode; onClick?: () => void; className?: string }) => {
  return (
    <div
      className={cn(
        "relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors focus:bg-slate-800 focus:text-slate-50 hover:bg-slate-800 hover:text-slate-50",
        className,
      )}
      onClick={onClick}
    >
      {children}
    </div>
  );
};
DropdownMenuItem.displayName = "DropdownMenuItem";

export { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem };
