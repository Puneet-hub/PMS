import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api, ApiError } from "../api";
import type { MaintenanceRequest, MaintenanceStatus, User } from "../types";
import { Badge, Button, Card, ErrorBanner, PageHeader, Select, Textarea } from "../components/ui";
import { useAuth } from "../AuthContext";

const STATUS_OPTIONS: MaintenanceStatus[] = ["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"];

export default function MaintenanceDetailPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const [request, setRequest] = useState<MaintenanceRequest | null>(null);
  const [managers, setManagers] = useState<User[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [comment, setComment] = useState("");
  const isManager = user?.role === "ADMIN" || user?.role === "PROPERTY_MANAGER";

  function load() {
    api
      .get<MaintenanceRequest>(`/maintenance-requests/${id}`)
      .then(setRequest)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load request"));
  }

  useEffect(load, [id]);

  useEffect(() => {
    if (isManager) {
      api.get<User[]>("/users").then((users) => setManagers(users.filter(u => u.role !== "TENANT"))).catch(() => {});
    }
  }, [isManager]);

  async function updateStatus(status: string) {
    setError(null);
    try {
      await api.patch(`/maintenance-requests/${id}`, { status });
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to update status");
    }
  }

  async function assignManager(managerId: string) {
    if (!managerId) return;
    setError(null);
    try {
      await api.patch(`/maintenance-requests/${id}`, { assigned_manager_id: Number(managerId) });
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to assign manager");
    }
  }

  async function submitComment(e: React.FormEvent) {
    e.preventDefault();
    if (!comment.trim()) return;
    setError(null);
    try {
      await api.post(`/maintenance-requests/${id}/comments`, { content: comment });
      setComment("");
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to add comment");
    }
  }

  if (!request) {
    return (
      <div>
        <ErrorBanner message={error} />
        <p className="text-sm text-slate-500">Loading…</p>
      </div>
    );
  }

  return (
    <div>
      <Link to="/maintenance" className="text-sm text-slate-500 hover:underline">← Back to Maintenance</Link>

      <PageHeader
        title={request.title}
        action={<div className="flex gap-2"><Badge value={request.priority} /><Badge value={request.status} /></div>}
      />
      <ErrorBanner message={error} />

      <Card className="mb-6">
        <div className="text-sm text-slate-500 mb-2">
          {request.unit.property?.title} — Unit {request.unit.unit_number}
        </div>
        <p className="text-slate-700">{request.description}</p>
        <div className="mt-3 text-xs text-slate-400">
          Filed by {request.created_by.name} on {new Date(request.created_at).toLocaleDateString()}
        </div>

        {isManager && (
          <div className="mt-4 flex flex-wrap gap-4 border-t border-slate-100 pt-4">
            <div>
              <div className="text-xs font-medium text-slate-500 mb-1">Status</div>
              <Select value={request.status} onChange={(e) => updateStatus(e.target.value)} className="w-auto">
                {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
              </Select>
            </div>
            <div>
              <div className="text-xs font-medium text-slate-500 mb-1">Assigned to</div>
              <Select
                value={request.assigned_manager_id ?? ""}
                onChange={(e) => assignManager(e.target.value)}
                className="w-auto"
              >
                <option value="">Unassigned</option>
                {managers.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
              </Select>
            </div>
          </div>
        )}
      </Card>

      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">Comments</h2>
      <div className="space-y-3 mb-4">
        {request.comments.map((c) => (
          <Card key={c.id} className="py-3">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
              <span className="font-medium text-slate-600">{c.author.name}</span>
              <span>{new Date(c.created_at).toLocaleString()}</span>
            </div>
            <p className="text-sm text-slate-700">{c.content}</p>
          </Card>
        ))}
        {request.comments.length === 0 && <p className="text-sm text-slate-500">No comments yet.</p>}
      </div>

      <form onSubmit={submitComment} className="flex gap-2">
        <Textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Add a comment…"
          rows={2}
          className="flex-1"
        />
        <Button type="submit">Post</Button>
      </form>
    </div>
  );
}
