from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    User,
    UserRole,
    Property,
    Unit,
    UnitStatus,
    Lease,
    Payment,
    PaymentStatus,
    MaintenanceRequest,
    MaintenanceStatus,
    MaintenancePriority,
)
from app.schemas import DashboardResponse
from app.security import require_role

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.PROPERTY_MANAGER)),
):
    """
    ADMIN sees stats across the whole system.
    PROPERTY_MANAGER sees stats scoped to only their own properties.
    """

    properties_query = db.query(Property)
    units_query = db.query(Unit)
    payments_query = db.query(Payment).join(Lease).join(Unit, Lease.unit_id == Unit.id)
    maintenance_query = db.query(MaintenanceRequest).join(Unit)

    if current_user.role == UserRole.PROPERTY_MANAGER:
        properties_query = properties_query.filter(Property.manager_id == current_user.id)
        units_query = units_query.join(Property).filter(Property.manager_id == current_user.id)
        payments_query = payments_query.join(Property, Unit.property_id == Property.id).filter(
            Property.manager_id == current_user.id
        )
        maintenance_query = maintenance_query.join(Property, Unit.property_id == Property.id).filter(
            Property.manager_id == current_user.id
        )

    units = units_query.all()
    payments = payments_query.all()
    maintenance_requests = maintenance_query.all()

    return DashboardResponse(
        total_properties=properties_query.count(),
        total_units=len(units),
        occupied_units=sum(1 for u in units if u.status == UnitStatus.OCCUPIED),
        available_units=sum(1 for u in units if u.status == UnitStatus.AVAILABLE),
        payments_paid=sum(1 for p in payments if p.status == PaymentStatus.PAID),
        payments_pending=sum(1 for p in payments if p.status == PaymentStatus.PENDING),
        payments_late=sum(1 for p in payments if p.status == PaymentStatus.LATE),
        maintenance_open=sum(1 for m in maintenance_requests if m.status == MaintenanceStatus.OPEN),
        maintenance_in_progress=sum(
            1 for m in maintenance_requests if m.status == MaintenanceStatus.IN_PROGRESS
        ),
        maintenance_high_urgent=sum(
            1
            for m in maintenance_requests
            if m.priority in (MaintenancePriority.HIGH, MaintenancePriority.URGENT)
        ),
    )
