import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { getProjects, createProject, updateProject, deleteProject, syncJira } from "@/api/projects";
import { toast } from "sonner";
import { RoleGate } from "@/auth/AuthProvider";

const empty = { name: "", total_budget: "", start_date: "", end_date: "", manager_id: "" };

export default function Projects() {
  const [projects, setProjects] = useState<any[]>([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<any>(empty);
  const [editingId, setEditingId] = useState<string | null>(null);

  const load = () => getProjects().then(setProjects).catch((e) => toast.error(e.message));
  useEffect(() => { load(); }, []);

  const submit = async () => {
    try {
      const payload = { ...form, total_budget: Number(form.total_budget) };
      if (editingId) await updateProject(editingId, payload);
      else await createProject(payload);
      toast.success(editingId ? "Project updated" : "Project created");
      setOpen(false); setForm(empty); setEditingId(null); load();
    } catch (e: any) { toast.error(e.message); }
  };

  const onEdit = (p: any) => { setEditingId(p.id); setForm({ ...empty, ...p }); setOpen(true); };
  const onDelete = async (id: string) => {
    if (!confirm("Delete this project?")) return;
    try { await deleteProject(id); toast.success("Deleted"); load(); } catch (e: any) { toast.error(e.message); }
  };
  const onSyncJira = async (id: string) => {
    try { await syncJira(id); toast.success("JIRA sync started"); } catch (e: any) { toast.error(e.message); }
  };

  return (
    <div className="space-y-8">
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Projects</h2>
          <p className="text-muted-foreground mt-1">Create and manage projects.</p>
        </div>
        <RoleGate allow={["Admin","Manager"]}>
        <Dialog open={open} onOpenChange={(o) => { setOpen(o); if (!o) { setEditingId(null); setForm(empty); } }}>
          <DialogTrigger asChild><Button className="bg-primary hover:bg-primary/90 shadow-soft">New Project</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>{editingId ? "Edit Project" : "New Project"}</DialogTitle></DialogHeader>
            <div className="grid gap-3">
              <div><Label>Name</Label><Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></div>
              <div><Label>Total Budget</Label><Input type="number" value={form.total_budget} onChange={(e) => setForm({ ...form, total_budget: e.target.value })} /></div>
              <div className="grid grid-cols-2 gap-3">
                <div><Label>Start Date</Label><Input type="date" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} /></div>
                <div><Label>End Date</Label><Input type="date" value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} /></div>
              </div>
              <div><Label>Manager ID</Label><Input value={form.manager_id} onChange={(e) => setForm({ ...form, manager_id: e.target.value })} /></div>
            </div>
            <DialogFooter><Button onClick={submit}>{editingId ? "Save" : "Create"}</Button></DialogFooter>
          </DialogContent>
        </Dialog>
        </RoleGate>
      </div>

      <Card className="card-elevated border-0">
        <CardHeader><CardTitle>All Projects</CardTitle></CardHeader>
        <CardContent>
          <div className="overflow-x-auto rounded-lg border">
          <Table>
            <TableHeader className="bg-muted/50">
              <TableRow>
                <TableHead>Name</TableHead><TableHead>Budget</TableHead><TableHead>Start</TableHead>
                <TableHead>End</TableHead><TableHead>Manager</TableHead><TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {projects.map((p) => (
                <TableRow key={p.id}>
                  <TableCell>{p.name}</TableCell>
                  <TableCell>${Number(p.total_budget ?? 0).toLocaleString()}</TableCell>
                  <TableCell>{p.start_date}</TableCell>
                  <TableCell>{p.end_date}</TableCell>
                  <TableCell>{p.manager_id}</TableCell>
                  <TableCell className="text-right space-x-2">
                    <RoleGate allow={["Admin","Manager"]}>
                      <Button size="sm" variant="outline" onClick={() => onSyncJira(p.id)}>Sync Jira</Button>
                      <Button size="sm" variant="outline" onClick={() => onEdit(p)}>Edit</Button>
                    </RoleGate>
                    <RoleGate allow={["Admin"]}>
                      <Button size="sm" variant="destructive" onClick={() => onDelete(p.id)}>Delete</Button>
                    </RoleGate>
                  </TableCell>
                </TableRow>
              ))}
              {!projects.length && <TableRow><TableCell colSpan={6} className="text-center text-muted-foreground py-8">No projects.</TableCell></TableRow>}
            </TableBody>
          </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
