import { useEffect, useState } from "react";
import { api, ApiError } from "../api";
import type { Dashboard } from "../types";
import { Card, ErrorBanner, PageHeader } from "../components/ui";

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <Card>
      <div className="text-sm text-slate-500">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-slate-900">{value}</div>
    </Card>
  );
}

export default function DashboardPage() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<Dashboard>("/dashboard")
      .then(setData)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load dashboard"));
  }, []);

  return (
    <div>
      <PageHeader title="Dashboard" />
      <ErrorBanner message={error} />

      {data && (
        <div className="space-y-8">
          <section>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">Properties</h2>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <Stat label="Total Properties" value={data.total_properties} />
              <Stat label="Total Units" value={data.total_units} />
              <Stat label="Occupied Units" value={data.occupied_units} />
              <Stat label="Available Units" value={data.available_units} />
            </div>
          </section>

          <section>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">Payments</h2>
            <div className="grid grid-cols-3 gap-4">
              <Stat label="Paid" value={data.payments_paid} />
              <Stat label="Pending" value={data.payments_pending} />
              <Stat label="Late" value={data.payments_late} />
            </div>
          </section>

          <section>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">Maintenance</h2>
            <div className="grid grid-cols-3 gap-4">
              <Stat label="Open" value={data.maintenance_open} />
              <Stat label="In Progress" value={data.maintenance_in_progress} />
              <Stat label="High / Urgent" value={data.maintenance_high_urgent} />
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
