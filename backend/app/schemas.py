from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field

from app.models import (
    UserRole,
    UnitStatus,
    LeaseStatus,
    PaymentStatus,
    MaintenancePriority,
    MaintenanceStatus,
)


# =========================================================
# USER
# =========================================================

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    role: UserRole
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: UserRole

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# =========================================================
# PROPERTY
# =========================================================

class PropertyCreate(BaseModel):
    title: str
    address: str


class PropertyResponse(BaseModel):
    id: int
    title: str
    address: str
    manager_id: int

    class Config:
        from_attributes = True


class PropertyBasicResponse(BaseModel):
    id: int
    title: str
    address: str

    class Config:
        from_attributes = True


class PropertyWithStatsResponse(PropertyResponse):
    total_units: int
    occupied_units: int
    available_units: int


# =========================================================
# UNIT
# =========================================================

class UnitCreate(BaseModel):
    property_id: int
    unit_number: str
    bedrooms: int = Field(ge=0)
    bathrooms: int = Field(ge=0)
    monthly_rent: int = Field(gt=0)
    status: UnitStatus = UnitStatus.AVAILABLE


class UnitUpdate(BaseModel):
    unit_number: str
    bedrooms: int = Field(ge=0)
    bathrooms: int = Field(ge=0)
    monthly_rent: int = Field(gt=0)
    status: UnitStatus


class UnitResponse(BaseModel):
    id: int
    property_id: int
    unit_number: str
    bedrooms: int
    bathrooms: int
    monthly_rent: int
    status: UnitStatus

    class Config:
        from_attributes = True


class UnitWithPropertyResponse(UnitResponse):
    property: PropertyBasicResponse


# =========================================================
# TENANT (thin view of a User with role=TENANT)
# =========================================================

class TenantResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: UserRole

    class Config:
        from_attributes = True


# =========================================================
# LEASE
# =========================================================

class LeaseCreate(BaseModel):
    tenant_id: int
    unit_id: int
    start_date: date
    end_date: date | None = None
    monthly_rent: int = Field(gt=0)
    security_deposit: int = Field(ge=0)


class LeaseUpdate(BaseModel):
    start_date: date
    end_date: date | None = None
    monthly_rent: int = Field(gt=0)
    security_deposit: int = Field(ge=0)
    status: LeaseStatus


class LeaseResponse(BaseModel):
    id: int
    tenant_id: int
    unit_id: int
    start_date: date
    end_date: date | None
    monthly_rent: int
    security_deposit: int
    status: LeaseStatus

    tenant: TenantResponse
    unit: UnitWithPropertyResponse

    class Config:
        from_attributes = True


# =========================================================
# PAYMENT
# =========================================================

class PaymentCreate(BaseModel):
    lease_id: int
    amount: int = Field(gt=0)
    due_date: date
    status: PaymentStatus = PaymentStatus.PENDING


class PaymentUpdate(BaseModel):
    amount: int = Field(gt=0)
    due_date: date
    paid_date: date | None = None
    status: PaymentStatus


class PaymentResponse(BaseModel):
    id: int
    lease_id: int
    amount: int
    due_date: date
    paid_date: date | None
    status: PaymentStatus

    class Config:
        from_attributes = True


class PaymentWithLeaseResponse(PaymentResponse):
    lease: LeaseResponse


# =========================================================
# MAINTENANCE COMMENT
# =========================================================

class MaintenanceCommentCreate(BaseModel):
    content: str = Field(min_length=1)


class MaintenanceCommentResponse(BaseModel):
    id: int
    maintenance_request_id: int
    author_id: int
    content: str
    created_at: datetime

    author: TenantResponse

    class Config:
        from_attributes = True


# =========================================================
# MAINTENANCE REQUEST
# =========================================================

class MaintenanceRequestCreate(BaseModel):
    unit_id: int
    title: str
    description: str
    priority: MaintenancePriority = MaintenancePriority.MEDIUM


class MaintenanceRequestUpdate(BaseModel):
    """Used by managers/admins to assign and change status."""
    status: MaintenanceStatus | None = None
    assigned_manager_id: int | None = None
    priority: MaintenancePriority | None = None


class MaintenanceRequestResponse(BaseModel):
    id: int
    unit_id: int
    created_by_id: int
    assigned_manager_id: int | None
    title: str
    description: str
    priority: MaintenancePriority
    status: MaintenanceStatus
    created_at: datetime
    updated_at: datetime

    unit: UnitWithPropertyResponse
    created_by: TenantResponse
    comments: list[MaintenanceCommentResponse] = []

    class Config:
        from_attributes = True


# =========================================================
# DASHBOARD
# =========================================================

class DashboardResponse(BaseModel):
    total_properties: int
    total_units: int
    occupied_units: int
    available_units: int

    payments_paid: int
    payments_pending: int
    payments_late: int

    maintenance_open: int
    maintenance_in_progress: int
    maintenance_high_urgent: int
