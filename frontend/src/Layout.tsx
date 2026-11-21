import { NavLink, Outlet, Navigate } from "react-router-dom";
import { useAuth } from "./AuthContext";

const NAV_ITEMS: { to: string; label: string; roles: string[] }[] = [
  { to: "/dashboard", label: "Dashboard", roles: ["ADMIN", "PROPERTY_MANAGER"] },
  { to: "/properties", label: "Properties", roles: ["ADMIN", "PROPERTY_MANAGER"] },
  { to: "/units", label: "Units", roles: ["ADMIN", "PROPERTY_MANAGER"] },
  { to: "/tenants", label: "Tenants", roles: ["ADMIN", "PROPERTY_MANAGER"] },
  { to: "/leases", label: "Leases", roles: ["ADMIN", "PROPERTY_MANAGER", "TENANT"] },
  { to: "/payments", label: "Payments", roles: ["ADMIN", "PROPERTY_MANAGER", "TENANT"] },
  { to: "/maintenance", label: "Maintenance", roles: ["ADMIN", "PROPERTY_MANAGER", "TENANT"] },
];

export default function Layout() {
  const { user, loading, logout } = useAuth();

  if (loading) {
    return <div className="flex h-screen items-center justify-center text-slate-500">Loading…</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  const items = NAV_ITEMS.filter((item) => item.roles.includes(user.role));

  return (
    <div className="flex min-h-screen">
      <aside className="w-56 shrink-0 border-r border-slate-200 bg-white p-4 flex flex-col">
        <div className="mb-6 px-2">
          <div className="text-lg font-semibold text-slate-900">PMS</div>
          <div className="text-xs text-slate-500">Property Management</div>
        </div>

        <nav className="flex-1 space-y-1">
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `block rounded-md px-3 py-2 text-sm font-medium ${
                  isActive
                    ? "bg-slate-900 text-white"
                    : "text-slate-600 hover:bg-slate-100"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-slate-200 pt-3 mt-3">
          <div className="px-2 text-sm text-slate-700">{user.name}</div>
          <div className="px-2 text-xs text-slate-400 mb-2">{user.role}</div>
          <button
            onClick={logout}
            className="w-full rounded-md px-3 py-2 text-left text-sm text-slate-600 hover:bg-slate-100"
          >
            Log out
          </button>
        </div>
      </aside>

      <main className="flex-1 p-8 max-w-6xl">
        <Outlet />
      </main>
    </div>
  );
}
