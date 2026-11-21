import { useEffect, useState } from "react";
import { api, ApiError } from "../api";
import type { Lease, Property, Unit, User } from "../types";
import { Badge, Button, Card, ErrorBanner, Field, Input, PageHeader, Select } from "../components/ui";
import { useAuth } from "../AuthContext";

export default function LeasesPage() {
  const { user } = useAuth();
  const [leases, setLeases] = useState<Lease[]>([]);
  const [error, setError] = useState<string | null>(null);

  function load() {
    api
      .get<Lease[]>("/leases")
      .then(setLeases)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load leases"));
  }

  useEffect(load, []);

  const isManager = user?.role === "ADMIN" || user?.role === "PROPERTY_MANAGER";

  return (
    <div>
      <PageHeader title="Leases" />
      <ErrorBanner message={error} />

      {isManager && <LeaseCreateForm onCreated={load} />}

      <div className="space-y-4">
        {leases.map((lease) => (
          <LeaseCard key={lease.id} lease={lease} isManager={isManager} onChanged={load} />
        ))}
        {leases.length === 0 && <p className="text-sm text-slate-500">No leases found.</p>}
      </div>
    </div>
  );
}

function LeaseCard({ lease, isManager, onChanged }: { lease: Lease; isManager: boolean; onChanged: () => void }) {
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState(lease.status);

  async function updateStatus(newStatus: string) {
    setError(null);
    try {
      await api.put(`/leases/${lease.id}`, {
        start_date: lease.start_date,
        end_date: lease.end_date,
        monthly_rent: lease.monthly_rent,
        security_deposit: lease.security_deposit,
        status: newStatus,
      });
      setStatus(newStatus as Lease["status"]);
      onChanged();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to update lease");
    }
  }

  return (
    <Card>
      <div className="flex items-start justify-between">
        <div>
          <div className="font-medium text-slate-900">
            {lease.unit.property?.title} — Unit {lease.unit.unit_number}
          </div>
          <div className="text-sm text-slate-500">{lease.tenant.name} ({lease.tenant.email})</div>
        </div>
        <Badge value={status} />
      </div>

      <div className="mt-3 grid grid-cols-2 gap-3 text-sm text-slate-600 sm:grid-cols-4">
        <div><span className="text-slate-400">Start:</span> {lease.start_date}</div>
        <div><span className="text-slate-400">End:</span> {lease.end_date ?? "Open-ended"}</div>
        <div><span className="text-slate-400">Rent:</span> ₹{lease.monthly_rent.toLocaleString()}</div>
        <div><span className="text-slate-400">Deposit:</span> ₹{lease.security_deposit.toLocaleString()}</div>
      </div>

      <ErrorBanner message={error} />

      {isManager && status === "ACTIVE" && (
        <div className="mt-3 flex gap-2">
          <Button variant="secondary" onClick={() => updateStatus("TERMINATED")}>Terminate</Button>
          <Button variant="secondary" onClick={() => updateStatus("EXPIRED")}>Mark Expired</Button>
        </div>
      )}
    </Card>
  );
}

function LeaseCreateForm({ onCreated }: { onCreated: () => void }) {
  const [show, setShow] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tenants, setTenants] = useState<User[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);

  const [tenantId, setTenantId] = useState("");
  const [unitId, setUnitId] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [rent, setRent] = useState("");
  const [deposit, setDeposit] = useState("");

  useEffect(() => {
    if (!show) return;
    api.get<User[]>("/users?role=TENANT").then(setTenants).catch(() => {});
    api.get<Property[]>("/properties").then(async (properties) => {
      const allUnits: Unit[] = [];
      for (const p of properties) {
        const propUnits = await api.get<Unit[]>(`/units?property_id=${p.id}`);
        allUnits.push(...propUnits);
      }
      setUnits(allUnits);
    }).catch(() => {});
  }, [show]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/leases", {
        tenant_id: Number(tenantId),
        unit_id: Number(unitId),
        start_date: startDate,
        end_date: endDate || null,
        monthly_rent: Number(rent),
        security_deposit: Number(deposit),
      });
      setShow(false);
      setTenantId(""); setUnitId(""); setStartDate(""); setEndDate(""); setRent(""); setDeposit("");
      onCreated();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create lease");
    }
  }

  return (
    <div className="mb-6">
      <Button onClick={() => setShow((v) => !v)}>{show ? "Cancel" : "Create Lease"}</Button>

      {show && (
        <Card className="mt-4">
          <ErrorBanner message={error} />
          <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-4 sm:grid-cols-3">
            <Field label="Tenant">
              <Select value={tenantId} onChange={(e) => setTenantId(e.target.value)} required>
                <option value="">Select tenant…</option>
                {tenants.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
              </Select>
            </Field>
            <Field label="Unit">
              <Select value={unitId} onChange={(e) => setUnitId(e.target.value)} required>
                <option value="">Select unit…</option>
                {units.map((u) => (
                  <option key={u.id} value={u.id}>{u.property?.title} — {u.unit_number}</option>
                ))}
              </Select>
            </Field>
            <Field label="Monthly Rent">
              <Input type="number" value={rent} onChange={(e) => setRent(e.target.value)} required />
            </Field>
            <Field label="Start Date">
              <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} required />
            </Field>
            <Field label="End Date (optional)">
              <Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
            </Field>
            <Field label="Security Deposit">
              <Input type="number" value={deposit} onChange={(e) => setDeposit(e.target.value)} required />
            </Field>
            <div className="col-span-2 sm:col-span-3">
              <Button type="submit">Create Lease</Button>
            </div>
          </form>
        </Card>
      )}
    </div>
  );
}
