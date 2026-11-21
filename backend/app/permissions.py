from fastapi import HTTPException, status

from app.models import User, UserRole, Property, Unit, Lease


def is_admin(user: User) -> bool:
    return user.role == UserRole.ADMIN


def ensure_property_access(property_obj: Property, user: User) -> None:
    """Admin: full access. PM: only their own properties. Tenant: never."""
    if is_admin(user):
        return

    if user.role == UserRole.PROPERTY_MANAGER and property_obj.manager_id == user.id:
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have access to this property",
    )


def ensure_unit_write_access(unit: Unit, user: User) -> None:
    """Admin or the PM who owns the unit's property can modify a unit."""
    ensure_property_access(unit.property, user)


def ensure_lease_manage_access(lease: Lease, user: User) -> None:
    """Admin or the PM who owns the lease's unit's property."""
    ensure_property_access(lease.unit.property, user)


def ensure_lease_view_access(lease: Lease, user: User) -> None:
    """Admin, the owning PM, or the tenant on the lease."""
    if is_admin(user):
        return

    if user.role == UserRole.PROPERTY_MANAGER and lease.unit.property.manager_id == user.id:
        return

    if user.role == UserRole.TENANT and lease.tenant_id == user.id:
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have access to this lease",
    )


def ensure_maintenance_view_access(request_obj, user: User) -> None:
    """Admin, the owning PM, or the tenant who created the request."""
    if is_admin(user):
        return

    if (
        user.role == UserRole.PROPERTY_MANAGER
        and request_obj.unit.property.manager_id == user.id
    ):
        return

    if user.role == UserRole.TENANT and request_obj.created_by_id == user.id:
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have access to this maintenance request",
    )
