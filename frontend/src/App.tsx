import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import AppLayout from "./layouts/AppLayout";
import Dashboard from "./pages/Dashboard";
import Projects from "./pages/Projects";
import Sprints from "./pages/Sprints";
import Tasks from "./pages/Tasks";
import EVMDashboard from "./pages/EVMDashboard";
import MLPredictions from "./pages/MLPredictions";
import Intelligence from "./pages/Intelligence";
import ProjectLedger from "./pages/ProjectLedger";
import { AuthProvider } from "./auth/AuthProvider";
import NotFound from "./pages/NotFound.tsx";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>
      <AuthProvider>
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <Routes>
            <Route element={<AppLayout />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/projects" element={<Projects />} />
              <Route path="/sprints" element={<Sprints />} />
              <Route path="/tasks" element={<Tasks />} />
              <Route path="/ledger" element={<ProjectLedger />} />
              <Route path="/evm" element={<EVMDashboard />} />
              <Route path="/intelligence" element={<Intelligence />} />
              <Route path="/ml" element={<MLPredictions />} />
            </Route>
            <Route path="*" element={<NotFound />} />
          </Routes>
        </TooltipProvider>
      </AuthProvider>
    </BrowserRouter>
  </QueryClientProvider>
);

export default App;
