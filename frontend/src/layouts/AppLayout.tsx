import { Outlet, useLocation } from "react-router-dom";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/AppSidebar";
import { Bell, Search, LogIn, LogOut, ShieldCheck } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useAuth, type Role } from "@/auth/AuthProvider";
import { isMockMode } from "@/api/axiosInstance";

const titles: Record<string, { title: string; subtitle: string }> = {
  "/":             { title: "Executive Dashboard", subtitle: "Portfolio-level Earned Value posture" },
  "/projects":     { title: "Projects",            subtitle: "Manage the project portfolio" },
  "/sprints":      { title: "Sprints",             subtitle: "Plan and track sprints per project" },
  "/tasks":        { title: "Tasks",               subtitle: "Granular task management" },
  "/ledger":       { title: "Project Ledger",      subtitle: "Task-level PV / EV / AC with SV, CV, SPI, CPI" },
  "/evm":          { title: "EVM Dashboard",       subtitle: "Earned Value Management insights" },
  "/intelligence": { title: "Intelligence",        subtitle: "Predictive analytics powered by Oracle 26ai" },
  "/ml":           { title: "ML Predictions",      subtitle: "Run individual predictive models" },
};

export default function AppLayout() {
  const { pathname } = useLocation();
  const meta =
    titles[pathname] ||
    titles[Object.keys(titles).find((k) => k !== "/" && pathname.startsWith(k)) ?? "/"] ||
    titles["/"];

  const { isAuthenticated, user, role, setRole, login, logout, authMode } = useAuth();

  const initials = (user?.name || user?.email || "U")
    .split(" ").map((s) => s[0]).slice(0, 2).join("").toUpperCase();

  return (
    <SidebarProvider defaultOpen={true}>
      <div className="min-h-screen flex w-full bg-background">
        <AppSidebar />
        <div className="flex-1 flex flex-col min-w-0">
          <header className="h-16 flex items-center gap-3 border-b bg-card/80 backdrop-blur-md px-4 sticky top-0 z-30">
            <SidebarTrigger className="h-9 w-9 rounded-md hover:bg-muted transition-colors" />
            <div className="hidden md:flex flex-col leading-tight">
              <h1 className="text-sm font-semibold text-foreground">{meta.title}</h1>
              <span className="text-xs text-muted-foreground">{meta.subtitle}</span>
            </div>
            <div className="ml-auto flex items-center gap-2">
              <div className="relative hidden lg:block">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input placeholder="Search projects, sprints, tasks…" className="pl-8 w-72 h-9 bg-background" />
              </div>

              {authMode === "mock" && (
                <Select value={role} onValueChange={(v) => setRole(v as Role)}>
                  <SelectTrigger className="h-9 w-[130px] text-xs">
                    <ShieldCheck className="h-3.5 w-3.5 mr-1.5" />
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Admin">Admin</SelectItem>
                    <SelectItem value="Manager">Manager</SelectItem>
                    <SelectItem value="Viewer">Viewer (Stakeholder)</SelectItem>
                  </SelectContent>
                </Select>
              )}
              {authMode === "auth0" && (
                <Badge variant="outline" className="h-7 gap-1 border-primary/30 bg-primary-soft text-primary">
                  <ShieldCheck className="h-3 w-3" /> {role}
                </Badge>
              )}

              {isMockMode && (
                <Badge variant="outline" className="h-7 hidden xl:inline-flex border-warning/40 bg-warning/10 text-warning">
                  Demo data
                </Badge>
              )}

              <button className="h-9 w-9 rounded-md hover:bg-muted flex items-center justify-center transition-colors">
                <Bell className="h-4 w-4 text-muted-foreground" />
              </button>

              {authMode === "auth0" && !isAuthenticated && (
                <Button size="sm" onClick={login} className="h-9 gap-1.5">
                  <LogIn className="h-4 w-4" /> Sign in
                </Button>
              )}
              {authMode === "auth0" && isAuthenticated && (
                <Button size="sm" variant="ghost" onClick={logout} className="h-9 gap-1.5">
                  <LogOut className="h-4 w-4" /> Sign out
                </Button>
              )}

              <div className="h-9 w-9 rounded-full bg-gradient-primary flex items-center justify-center text-primary-foreground text-xs font-bold shadow-soft">
                {initials}
              </div>
            </div>
          </header>
          <main className="flex-1 p-6 md:p-8 animate-fade-in max-w-[1600px] w-full mx-auto">
            <Outlet />
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
}
