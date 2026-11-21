export type UserRole = "ADMIN" | "PROPERTY_MANAGER" | "TENANT";
export type UnitStatus = "AVAILABLE" | "OCCUPIED" | "MAINTENANCE";
export type LeaseStatus = "ACTIVE" | "EXPIRED" | "TERMINATED";
export type PaymentStatus = "PENDING" | "PAID" | "LATE";
export type MaintenancePriority = "LOW" | "MEDIUM" | "HIGH" | "URGENT";
export type MaintenanceStatus = "OPEN" | "IN_PROGRESS" | "RESOLVED" | "CLOSED";

export interface User {
  id: number;
  name: string;
  email: string;
  role: UserRole;
}

export interface Property {
  id: number;
  title: string;
  address: string;
  manager_id: number;
  total_units: number;
  occupied_units: number;
  available_units: number;
}

export interface Unit {
  id: number;
  property_id: number;
  unit_number: string;
  bedrooms: number;
  bathrooms: number;
  monthly_rent: number;
  status: UnitStatus;
  property?: { id: number; title: string; address: string };
}

export interface Lease {
  id: number;
  tenant_id: number;
  unit_id: number;
  start_date: string;
  end_date: string | null;
  monthly_rent: number;
  security_deposit: number;
  status: LeaseStatus;
  tenant: User;
  unit: Unit;
}

export interface Payment {
  id: number;
  lease_id: number;
  amount: number;
  due_date: string;
  paid_date: string | null;
  status: PaymentStatus;
}

export interface MaintenanceComment {
  id: number;
  maintenance_request_id: number;
  author_id: number;
  content: string;
  created_at: string;
  author: User;
}

export interface MaintenanceRequest {
  id: number;
  unit_id: number;
  created_by_id: number;
  assigned_manager_id: number | null;
  title: string;
  description: string;
  priority: MaintenancePriority;
  status: MaintenanceStatus;
  created_at: string;
  updated_at: string;
  unit: Unit;
  created_by: User;
  comments: MaintenanceComment[];
}

export interface Dashboard {
  total_properties: number;
  total_units: number;
  occupied_units: number;
  available_units: number;
  payments_paid: number;
  payments_pending: number;
  payments_late: number;
  maintenance_open: number;
  maintenance_in_progress: number;
  maintenance_high_urgent: number;
}
