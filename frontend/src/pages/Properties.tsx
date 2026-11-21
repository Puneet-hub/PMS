import { useEffect, useState } from "react";
import { api, ApiError } from "../api";
import type { Property } from "../types";
import { Button, Card, ErrorBanner, Field, Input, PageHeader } from "../components/ui";

export default function PropertiesPage() {
  const [properties, setProperties] = useState<Property[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState("");
  const [address, setAddress] = useState("");

  function load() {
    const query = search ? `?search=${encodeURIComponent(search)}` : "";
    api
      .get<Property[]>(`/properties${query}`)
      .then(setProperties)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load properties"));
  }

  useEffect(load, [search]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/properties", { title, address });
      setTitle("");
      setAddress("");
      setShowForm(false);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create property");
    }
  }

  return (
    <div>
      <PageHeader
        title="Properties"
        action={<Button onClick={() => setShowForm((v) => !v)}>{showForm ? "Cancel" : "Add Property"}</Button>}
      />
      <ErrorBanner message={error} />

      {showForm && (
        <Card className="mb-6">
          <form onSubmit={handleCreate} className="grid grid-cols-2 gap-4">
            <Field label="Title">
              <Input value={title} onChange={(e) => setTitle(e.target.value)} required />
            </Field>
            <Field label="Address">
              <Input value={address} onChange={(e) => setAddress(e.target.value)} required />
            </Field>
            <div className="col-span-2">
              <Button type="submit">Create Property</Button>
            </div>
          </form>
        </Card>
      )}

      <Input
        placeholder="Search by title or address…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="mb-4 max-w-sm"
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {properties.map((p) => (
          <Card key={p.id}>
            <div className="flex items-start justify-between">
              <div>
                <div className="font-medium text-slate-900">{p.title}</div>
                <div className="text-sm text-slate-500">{p.address}</div>
              </div>
            </div>
            <div className="mt-3 flex gap-4 text-sm text-slate-600">
              <span>{p.total_units} units</span>
              <span>{p.occupied_units} occupied</span>
              <span>{p.available_units} available</span>
            </div>
          </Card>
        ))}
        {properties.length === 0 && (
          <p className="text-sm text-slate-500">No properties found.</p>
        )}
      </div>
    </div>
  );
}
