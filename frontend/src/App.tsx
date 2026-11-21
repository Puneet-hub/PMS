import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import type { ReactNode } from "react";
import { AuthProvider, useAuth } from "./AuthContext";
import { homePathFor } from "./roles";
import Layout from "./Layout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Properties from "./pages/Properties";
import Units from "./pages/Units";
import Tenants from "./pages/Tenants";
import Leases from "./pages/Leases";
import Payments from "./pages/Payments";
import Maintenance from "./pages/Maintenance";
import MaintenanceDetail from "./pages/MaintenanceDetail";

// Send the user to the right landing page for their role.
function HomeRedirect() {
  const { user, loading } = useAuth();
  if (loading) return null;
  return <Navigate to={user ? homePathFor(user.role) : "/login"} replace />;
}

// Pages whose backing API endpoints are admin/manager only.
function ManagerOnly({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  if (user?.role === "TENANT") return <Navigate to={homePathFor(user.role)} replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />

          <Route element={<Layout />}>
            <Route path="/" element={<HomeRedirect />} />
            <Route path="/dashboard" element={<ManagerOnly><Dashboard /></ManagerOnly>} />
            <Route path="/properties" element={<ManagerOnly><Properties /></ManagerOnly>} />
            <Route path="/units" element={<ManagerOnly><Units /></ManagerOnly>} />
            <Route path="/tenants" element={<ManagerOnly><Tenants /></ManagerOnly>} />
            <Route path="/leases" element={<Leases />} />
            <Route path="/payments" element={<Payments />} />
            <Route path="/maintenance" element={<Maintenance />} />
            <Route path="/maintenance/:id" element={<MaintenanceDetail />} />
          </Route>

          <Route path="*" element={<HomeRedirect />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
