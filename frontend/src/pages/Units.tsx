import { useEffect, useState } from "react";
import { api, ApiError } from "../api";
import type { Property, Unit, UnitStatus } from "../types";
import { Badge, Button, Card, ErrorBanner, Field, Input, PageHeader, Select } from "../components/ui";

const STATUS_OPTIONS: UnitStatus[] = ["AVAILABLE", "OCCUPIED", "MAINTENANCE"];

export default function UnitsPage() {
  const [units, setUnits] = useState<Unit[]>([]);
  const [properties, setProperties] = useState<Property[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [propertyFilter, setPropertyFilter] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  const [propertyId, setPropertyId] = useState("");
  const [unitNumber, setUnitNumber] = useState("");
  const [bedrooms, setBedrooms] = useState("1");
  const [bathrooms, setBathrooms] = useState("1");
  const [rent, setRent] = useState("");

  useEffect(() => {
    api.get<Property[]>("/properties").then(setProperties).catch(() => {});
  }, []);

  function load() {
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (statusFilter) params.set("status", statusFilter);
    if (propertyFilter) params.set("property_id", propertyFilter);

    api
      .get<Unit[]>(`/units?${params.toString()}`)
      .then(setUnits)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load units"));
  }

  useEffect(load, [search, statusFilter, propertyFilter]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/units", {
        property_id: Number(propertyId),
        unit_number: unitNumber,
        bedrooms: Number(bedrooms),
        bathrooms: Number(bathrooms),
        monthly_rent: Number(rent),
      });
      setUnitNumber("");
      setRent("");
      setShowForm(false);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create unit");
    }
  }

  return (
    <div>
      <PageHeader
        title="Units"
        action={<Button onClick={() => setShowForm((v) => !v)}>{showForm ? "Cancel" : "Add Unit"}</Button>}
      />
      <ErrorBanner message={error} />

      {showForm && (
        <Card className="mb-6">
          <form onSubmit={handleCreate} className="grid grid-cols-2 gap-4 sm:grid-cols-3">
            <Field label="Property">
              <Select value={propertyId} onChange={(e) => setPropertyId(e.target.value)} required>
                <option value="">Select property…</option>
                {properties.map((p) => (
                  <option key={p.id} value={p.id}>{p.title}</option>
                ))}
              </Select>
            </Field>
            <Field label="Unit Number">
              <Input value={unitNumber} onChange={(e) => setUnitNumber(e.target.value)} required />
            </Field>
            <Field label="Monthly Rent">
              <Input type="number" value={rent} onChange={(e) => setRent(e.target.value)} required />
            </Field>
            <Field label="Bedrooms">
              <Input type="number" value={bedrooms} onChange={(e) => setBedrooms(e.target.value)} required />
            </Field>
            <Field label="Bathrooms">
              <Input type="number" value={bathrooms} onChange={(e) => setBathrooms(e.target.value)} required />
            </Field>
            <div className="col-span-2 sm:col-span-3">
              <Button type="submit">Create Unit</Button>
            </div>
          </form>
        </Card>
      )}

      <div className="mb-4 flex flex-wrap gap-3">
        <Input placeholder="Search unit number…" value={search} onChange={(e) => setSearch(e.target.value)} className="max-w-xs" />
        <Select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="w-auto">
          <option value="">All statuses</option>
          {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
        </Select>
        <Select value={propertyFilter} onChange={(e) => setPropertyFilter(e.target.value)} className="w-auto">
          <option value="">All properties</option>
          {properties.map((p) => <option key={p.id} value={p.id}>{p.title}</option>)}
        </Select>
      </div>

      <Card className="overflow-hidden p-0">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Unit</th>
              <th className="px-4 py-3">Property</th>
              <th className="px-4 py-3">Beds / Baths</th>
              <th className="px-4 py-3">Rent</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {units.map((u) => (
              <tr key={u.id} className="border-t border-slate-100">
                <td className="px-4 py-3 font-medium text-slate-900">{u.unit_number}</td>
                <td className="px-4 py-3 text-slate-600">{u.property?.title}</td>
                <td className="px-4 py-3 text-slate-600">{u.bedrooms} bd / {u.bathrooms} ba</td>
                <td className="px-4 py-3 text-slate-600">₹{u.monthly_rent.toLocaleString()}</td>
                <td className="px-4 py-3"><Badge value={u.status} /></td>
              </tr>
            ))}
            {units.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-6 text-center text-slate-500">No units found.</td></tr>
            )}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
