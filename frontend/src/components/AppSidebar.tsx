import { LayoutDashboard, FolderKanban, CalendarRange, ListChecks, LineChart, Brain, BookOpen, Sparkles, Shield } from "lucide-react";
import { NavLink, useLocation } from "react-router-dom";
import {
  Sidebar, SidebarContent, SidebarGroup, SidebarGroupContent, SidebarGroupLabel,
  SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarHeader, SidebarFooter, useSidebar,
} from "@/components/ui/sidebar";
import { cn } from "@/lib/utils";
import { useAuth, type Role } from "@/auth/AuthProvider";

type Item = { title: string; url: string; icon: any; allow: Role[] };

const items: Item[] = [
  { title: "Dashboard",       url: "/",             icon: LayoutDashboard, allow: ["Admin","Manager","Viewer"] },
  { title: "Projects",        url: "/projects",     icon: FolderKanban,    allow: ["Admin","Manager","Viewer"] },
  { title: "Sprints",         url: "/sprints",      icon: CalendarRange,   allow: ["Admin","Manager","Viewer"] },
  { title: "Tasks",           url: "/tasks",        icon: ListChecks,      allow: ["Admin","Manager"] },
  { title: "Project Ledger",  url: "/ledger",       icon: BookOpen,        allow: ["Admin","Manager","Viewer"] },
  { title: "EVM Dashboard",   url: "/evm",          icon: LineChart,       allow: ["Admin","Manager","Viewer"] },
  { title: "Intelligence",    url: "/intelligence", icon: Brain,           allow: ["Admin","Manager","Viewer"] },
  { title: "ML Predictions",  url: "/ml",           icon: Sparkles,        allow: ["Admin","Manager"] },
];

export function AppSidebar() {
  const { state } = useSidebar();
  const collapsed = state === "collapsed";
  const { pathname } = useLocation();
  const { role } = useAuth();
  const isActive = (path: string) => (path === "/" ? pathname === "/" : pathname.startsWith(path));

  return (
    <Sidebar collapsible="icon" className="border-r border-sidebar-border">
      <SidebarHeader className="border-b border-sidebar-border">
        <div className={cn("flex items-center gap-2 px-2 py-3", collapsed && "justify-center px-0")}>
          <div className="h-9 w-9 rounded-md bg-primary flex items-center justify-center shadow-elevated">
            <Shield className="h-4 w-4 text-primary-foreground" />
          </div>
          {!collapsed && (
            <div className="flex flex-col leading-tight">
              <span className="text-sm font-bold text-sidebar-foreground tracking-tight">SmartEVM</span>
              <span className="text-[10px] uppercase tracking-widest text-sidebar-foreground/50">Oracle 26ai</span>
            </div>
          )}
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          {!collapsed && <SidebarGroupLabel className="text-sidebar-foreground/40 text-[10px] uppercase tracking-widest">Workspace</SidebarGroupLabel>}
          <SidebarGroupContent>
            <SidebarMenu>
              {items.filter((i) => i.allow.includes(role)).map((item) => {
                const active = isActive(item.url);
                return (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton asChild isActive={active} tooltip={item.title}>
                      <NavLink
                        to={item.url}
                        className={cn(
                          "group flex items-center gap-3 rounded-md px-3 py-2 transition-all",
                          "text-sidebar-foreground/75 hover:text-sidebar-foreground hover:bg-sidebar-accent",
                          active && "bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground shadow-soft"
                        )}
                      >
                        <item.icon className={cn("h-4 w-4 shrink-0", active && "text-primary-foreground")} />
                        {!collapsed && <span className="text-sm font-medium">{item.title}</span>}
                      </NavLink>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="border-t border-sidebar-border">
        {!collapsed ? (
          <div className="px-3 py-2 text-[10px] text-sidebar-foreground/50 uppercase tracking-widest">v2.0 · Slate &amp; Steel</div>
        ) : (
          <div className="flex justify-center py-2"><span className="h-2 w-2 rounded-full bg-success" /></div>
        )}
      </SidebarFooter>
    </Sidebar>
  );
}
