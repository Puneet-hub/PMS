import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api";
import type { Lease, MaintenancePriority, MaintenanceRequest, MaintenanceStatus } from "../types";
import { Badge, Button, Card, ErrorBanner, Field, PageHeader, Select, Textarea, Input } from "../components/ui";
import { useAuth } from "../AuthContext";

const STATUS_OPTIONS: MaintenanceStatus[] = ["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"];
const PRIORITY_OPTIONS: MaintenancePriority[] = ["LOW", "MEDIUM", "HIGH", "URGENT"];

export default function MaintenancePage() {
  const { user } = useAuth();
  const [requests, setRequests] = useState<MaintenanceRequest[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [error, setError] = useState<string | null>(null);
  const isManager = user?.role === "ADMIN" || user?.role === "PROPERTY_MANAGER";

  function load() {
    const params = new URLSearchParams();
    if (statusFilter) params.set("status", statusFilter);
    if (priorityFilter) params.set("priority", priorityFilter);

    api
      .get<MaintenanceRequest[]>(`/maintenance-requests?${params.toString()}`)
      .then(setRequests)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load maintenance requests"));
  }

  useEffect(load, [statusFilter, priorityFilter]);

  return (
    <div>
      <PageHeader title="Maintenance Requests" />
      <ErrorBanner message={error} />

      {!isManager && <CreateRequestForm onCreated={load} />}

      <div className="mb-4 flex gap-3">
        <Select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="w-auto">
          <option value="">All statuses</option>
          {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
        </Select>
        <Select value={priorityFilter} onChange={(e) => setPriorityFilter(e.target.value)} className="w-auto">
          <option value="">All priorities</option>
          {PRIORITY_OPTIONS.map((p) => <option key={p} value={p}>{p}</option>)}
        </Select>
      </div>

      <div className="space-y-3">
        {requests.map((r) => (
          <Link key={r.id} to={`/maintenance/${r.id}`}>
            <Card className="hover:border-slate-300 transition-colors">
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-medium text-slate-900">{r.title}</div>
                  <div className="text-sm text-slate-500">
                    {r.unit.property?.title} — Unit {r.unit.unit_number}
                  </div>
                </div>
                <div className="flex gap-2">
                  <Badge value={r.priority} />
                  <Badge value={r.status} />
                </div>
              </div>
            </Card>
          </Link>
        ))}
        {requests.length === 0 && <p className="text-sm text-slate-500">No maintenance requests found.</p>}
      </div>
    </div>
  );
}

function CreateRequestForm({ onCreated }: { onCreated: () => void }) {
  const [show, setShow] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [leases, setLeases] = useState<Lease[]>([]);
  const [unitId, setUnitId] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState<MaintenancePriority>("MEDIUM");

  useEffect(() => {
    if (!show) return;
    api.get<Lease[]>("/leases?status=ACTIVE").then(setLeases).catch(() => {});
  }, [show]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/maintenance-requests", { unit_id: Number(unitId), title, description, priority });
      setShow(false);
      setUnitId(""); setTitle(""); setDescription(""); setPriority("MEDIUM");
      onCreated();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create request");
    }
  }

  return (
    <div className="mb-6">
      <Button onClick={() => setShow((v) => !v)}>{show ? "Cancel" : "New Request"}</Button>

      {show && (
        <Card className="mt-4">
          <ErrorBanner message={error} />
          <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-4">
            <Field label="Unit">
              <Select value={unitId} onChange={(e) => setUnitId(e.target.value)} required>
                <option value="">Select your unit…</option>
                {leases.map((l) => (
                  <option key={l.unit.id} value={l.unit.id}>
                    {l.unit.property?.title} — {l.unit.unit_number}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Priority">
              <Select value={priority} onChange={(e) => setPriority(e.target.value as MaintenancePriority)}>
                {PRIORITY_OPTIONS.map((p) => <option key={p} value={p}>{p}</option>)}
              </Select>
            </Field>
            <div className="col-span-2">
              <Field label="Title">
                <Input value={title} onChange={(e) => setTitle(e.target.value)} required />
              </Field>
            </div>
            <div className="col-span-2">
              <Field label="Description">
                <Textarea value={description} onChange={(e) => setDescription(e.target.value)} required rows={3} />
              </Field>
            </div>
            <div className="col-span-2">
              <Button type="submit">Submit Request</Button>
            </div>
          </form>
        </Card>
      )}
    </div>
  );
}
