from datetime import date, datetime
from enum import Enum

from sqlalchemy import String, ForeignKey, Text, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.base import Base


# =========================================================
# ENUMS
# =========================================================

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    PROPERTY_MANAGER = "PROPERTY_MANAGER"
    TENANT = "TENANT"


class UnitStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    MAINTENANCE = "MAINTENANCE"


class LeaseStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    TERMINATED = "TERMINATED"


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    LATE = "LATE"


class MaintenancePriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class MaintenanceStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


# =========================================================
# USER
# =========================================================

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True
    )
    role: Mapped[UserRole]
    password_hash: Mapped[str] = mapped_column(String(255))

    # User -> Properties managed by this user (as Property Manager)
    properties: Mapped[list["Property"]] = relationship(
        back_populates="manager"
    )

    # User -> Leases where this user is the tenant
    leases: Mapped[list["Lease"]] = relationship(
        back_populates="tenant"
    )

    # Maintenance requests this user created (as tenant)
    maintenance_requests_created: Mapped[list["MaintenanceRequest"]] = relationship(
        back_populates="created_by",
        foreign_keys="MaintenanceRequest.created_by_id"
    )

    # Maintenance requests assigned to this user (as manager)
    maintenance_requests_assigned: Mapped[list["MaintenanceRequest"]] = relationship(
        back_populates="assigned_manager",
        foreign_keys="MaintenanceRequest.assigned_manager_id"
    )

    comments: Mapped[list["MaintenanceComment"]] = relationship(
        back_populates="author"
    )


# =========================================================
# PROPERTY
# =========================================================

class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    address: Mapped[str] = mapped_column(String(500))

    manager_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    # Property -> Manager
    manager: Mapped["User"] = relationship(
        back_populates="properties"
    )

    # Property -> Units
    units: Mapped[list["Unit"]] = relationship(
        back_populates="property",
        cascade="all, delete-orphan"
    )


# =========================================================
# UNIT
# =========================================================

class Unit(Base):
    __tablename__ = "units"

    id: Mapped[int] = mapped_column(primary_key=True)

    property_id: Mapped[int] = mapped_column(
        ForeignKey("properties.id"),
        index=True
    )

    unit_number: Mapped[str] = mapped_column(String(50))
    bedrooms: Mapped[int]
    bathrooms: Mapped[int]
    monthly_rent: Mapped[int]
    status: Mapped[UnitStatus] = mapped_column(default=UnitStatus.AVAILABLE)

    # Unit -> Property
    property: Mapped["Property"] = relationship(
        back_populates="units"
    )

    # Unit -> Leases (history of leases on this unit)
    leases: Mapped[list["Lease"]] = relationship(
        back_populates="unit",
        cascade="all, delete-orphan"
    )

    # Unit -> Maintenance requests
    maintenance_requests: Mapped[list["MaintenanceRequest"]] = relationship(
        back_populates="unit",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_units_property_unit_number", "property_id", "unit_number"),
    )


# =========================================================
# LEASE
# =========================================================

class Lease(Base):
    """
    A Lease ties a tenant to a specific unit for a date range.

    Business rule (enforced in app/services/leases.py, not just here):
    a unit cannot have two overlapping ACTIVE leases.
    """

    __tablename__ = "leases"

    id: Mapped[int] = mapped_column(primary_key=True)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True
    )

    unit_id: Mapped[int] = mapped_column(
        ForeignKey("units.id"),
        index=True
    )

    start_date: Mapped[date]
    end_date: Mapped[date | None]

    monthly_rent: Mapped[int]
    security_deposit: Mapped[int]
    status: Mapped[LeaseStatus] = mapped_column(default=LeaseStatus.ACTIVE)

    # Lease -> Tenant
    tenant: Mapped["User"] = relationship(
        back_populates="leases"
    )

    # Lease -> Unit
    unit: Mapped["Unit"] = relationship(
        back_populates="leases"
    )

    # Lease -> Payments
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="lease",
        cascade="all, delete-orphan"
    )


# =========================================================
# PAYMENT
# =========================================================

class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)

    lease_id: Mapped[int] = mapped_column(
        ForeignKey("leases.id"),
        index=True
    )

    amount: Mapped[int]
    due_date: Mapped[date]
    paid_date: Mapped[date | None]
    status: Mapped[PaymentStatus] = mapped_column(default=PaymentStatus.PENDING)

    # Payment -> Lease
    lease: Mapped["Lease"] = relationship(
        back_populates="payments"
    )


# =========================================================
# MAINTENANCE REQUEST
# =========================================================

class MaintenanceRequest(Base):
    __tablename__ = "maintenance_requests"

    id: Mapped[int] = mapped_column(primary_key=True)

    unit_id: Mapped[int] = mapped_column(
        ForeignKey("units.id"),
        index=True
    )

    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    assigned_manager_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id")
    )

    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    priority: Mapped[MaintenancePriority] = mapped_column(
        default=MaintenancePriority.MEDIUM
    )
    status: Mapped[MaintenanceStatus] = mapped_column(
        default=MaintenanceStatus.OPEN
    )

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now()
    )

    # MaintenanceRequest -> Unit
    unit: Mapped["Unit"] = relationship(
        back_populates="maintenance_requests"
    )

    # MaintenanceRequest -> Creator (tenant)
    created_by: Mapped["User"] = relationship(
        back_populates="maintenance_requests_created",
        foreign_keys=[created_by_id]
    )

    # MaintenanceRequest -> Assigned manager
    assigned_manager: Mapped["User | None"] = relationship(
        back_populates="maintenance_requests_assigned",
        foreign_keys=[assigned_manager_id]
    )

    comments: Mapped[list["MaintenanceComment"]] = relationship(
        back_populates="maintenance_request",
        cascade="all, delete-orphan",
        order_by="MaintenanceComment.created_at"
    )


# =========================================================
# MAINTENANCE COMMENT
# =========================================================

class MaintenanceComment(Base):
    __tablename__ = "maintenance_comments"

    id: Mapped[int] = mapped_column(primary_key=True)

    maintenance_request_id: Mapped[int] = mapped_column(
        ForeignKey("maintenance_requests.id"),
        index=True
    )

    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    maintenance_request: Mapped["MaintenanceRequest"] = relationship(
        back_populates="comments"
    )

    author: Mapped["User"] = relationship(
        back_populates="comments"
    )
