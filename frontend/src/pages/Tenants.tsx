import { useEffect, useState } from "react";
import { api, ApiError } from "../api";
import type { User } from "../types";
import { Button, Card, ErrorBanner, Field, Input, PageHeader } from "../components/ui";

export default function TenantsPage() {
  const [tenants, setTenants] = useState<User[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  function load() {
    api
      .get<User[]>("/users?role=TENANT")
      .then(setTenants)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load tenants"));
  }

  useEffect(load, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/users", { name, email, password, role: "TENANT" });
      setName("");
      setEmail("");
      setPassword("");
      setShowForm(false);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create tenant");
    }
  }

  return (
    <div>
      <PageHeader
        title="Tenants"
        action={<Button onClick={() => setShowForm((v) => !v)}>{showForm ? "Cancel" : "Add Tenant"}</Button>}
      />
      <ErrorBanner message={error} />

      {showForm && (
        <Card className="mb-6">
          <form onSubmit={handleCreate} className="grid grid-cols-3 gap-4">
            <Field label="Full name">
              <Input value={name} onChange={(e) => setName(e.target.value)} required />
            </Field>
            <Field label="Email">
              <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </Field>
            <Field label="Temporary password">
              <Input value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} />
            </Field>
            <div className="col-span-3">
              <Button type="submit">Create Tenant</Button>
            </div>
          </form>
        </Card>
      )}

      <Card className="overflow-hidden p-0">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Email</th>
            </tr>
          </thead>
          <tbody>
            {tenants.map((t) => (
              <tr key={t.id} className="border-t border-slate-100">
                <td className="px-4 py-3 font-medium text-slate-900">{t.name}</td>
                <td className="px-4 py-3 text-slate-600">{t.email}</td>
              </tr>
            ))}
            {tenants.length === 0 && (
              <tr><td colSpan={2} className="px-4 py-6 text-center text-slate-500">No tenants found.</td></tr>
            )}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
