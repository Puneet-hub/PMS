import type { UserRole } from "./types";

// Where each role lands after login (and when hitting "/" or an unknown URL).
// Tenants cannot access the dashboard API, so they start on their leases.
export function homePathFor(role: UserRole): string {
  return role === "TENANT" ? "/leases" : "/dashboard";
}
