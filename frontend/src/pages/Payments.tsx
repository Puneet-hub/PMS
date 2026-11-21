import { useEffect, useState } from "react";
import { api, ApiError } from "../api";
import type { Lease, Payment } from "../types";
import { Badge, Button, Card, ErrorBanner, Field, Input, PageHeader, Select } from "../components/ui";
import { useAuth } from "../AuthContext";

export default function PaymentsPage() {
  const { user } = useAuth();
  const [payments, setPayments] = useState<Payment[]>([]);
  const [error, setError] = useState<string | null>(null);
  const isManager = user?.role === "ADMIN" || user?.role === "PROPERTY_MANAGER";

  function load() {
    api
      .get<Payment[]>("/payments")
      .then(setPayments)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load payments"));
  }

  useEffect(load, []);

  return (
    <div>
      <PageHeader title="Payments" />
      <ErrorBanner message={error} />

      {isManager && <PaymentCreateForm onCreated={load} />}

      <Card className="overflow-hidden p-0">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Amount</th>
              <th className="px-4 py-3">Due Date</th>
              <th className="px-4 py-3">Paid Date</th>
              <th className="px-4 py-3">Status</th>
              {isManager && <th className="px-4 py-3"></th>}
            </tr>
          </thead>
          <tbody>
            {payments.map((p) => (
              <PaymentRow key={p.id} payment={p} isManager={isManager} onChanged={load} />
            ))}
            {payments.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-6 text-center text-slate-500">No payments found.</td></tr>
            )}
          </tbody>
        </table>
      </Card>
    </div>
  );
}

function PaymentRow({ payment, isManager, onChanged }: { payment: Payment; isManager: boolean; onChanged: () => void }) {
  const [error, setError] = useState<string | null>(null);

  async function markPaid() {
    setError(null);
    try {
      await api.put(`/payments/${payment.id}`, {
        amount: payment.amount,
        due_date: payment.due_date,
        paid_date: new Date().toISOString().slice(0, 10),
        status: "PAID",
      });
      onChanged();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to update payment");
    }
  }

  return (
    <tr className="border-t border-slate-100">
      <td className="px-4 py-3 font-medium text-slate-900">₹{payment.amount.toLocaleString()}</td>
      <td className="px-4 py-3 text-slate-600">{payment.due_date}</td>
      <td className="px-4 py-3 text-slate-600">{payment.paid_date ?? "—"}</td>
      <td className="px-4 py-3"><Badge value={payment.status} /></td>
      {isManager && (
        <td className="px-4 py-3">
          {payment.status !== "PAID" && (
            <Button variant="secondary" onClick={markPaid}>Mark Paid</Button>
          )}
          {error && <div className="text-xs text-red-600 mt-1">{error}</div>}
        </td>
      )}
    </tr>
  );
}

function PaymentCreateForm({ onCreated }: { onCreated: () => void }) {
  const [show, setShow] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [leases, setLeases] = useState<Lease[]>([]);
  const [leaseId, setLeaseId] = useState("");
  const [amount, setAmount] = useState("");
  const [dueDate, setDueDate] = useState("");

  useEffect(() => {
    if (!show) return;
    api.get<Lease[]>("/leases?status=ACTIVE").then(setLeases).catch(() => {});
  }, [show]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/payments", { lease_id: Number(leaseId), amount: Number(amount), due_date: dueDate });
      setShow(false);
      setLeaseId(""); setAmount(""); setDueDate("");
      onCreated();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create payment");
    }
  }

  return (
    <div className="mb-6">
      <Button onClick={() => setShow((v) => !v)}>{show ? "Cancel" : "Add Payment"}</Button>

      {show && (
        <Card className="mt-4">
          <ErrorBanner message={error} />
          <form onSubmit={handleSubmit} className="grid grid-cols-3 gap-4">
            <Field label="Lease">
              <Select value={leaseId} onChange={(e) => setLeaseId(e.target.value)} required>
                <option value="">Select lease…</option>
                {leases.map((l) => (
                  <option key={l.id} value={l.id}>
                    {l.tenant.name} — {l.unit.property?.title} {l.unit.unit_number}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Amount">
              <Input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} required />
            </Field>
            <Field label="Due Date">
              <Input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} required />
            </Field>
            <div className="col-span-3">
              <Button type="submit">Create Payment</Button>
            </div>
          </form>
        </Card>
      )}
    </div>
  );
}
