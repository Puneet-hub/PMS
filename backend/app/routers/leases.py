from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole, Unit, UnitStatus, Lease, LeaseStatus
from app.permissions import ensure_lease_manage_access, ensure_lease_view_access, ensure_property_access
from app.schemas import LeaseCreate, LeaseUpdate, LeaseResponse
from app.security import get_current_user, require_role
from app.services.leases import check_lease_overlap

router = APIRouter(prefix="/leases", tags=["leases"])


def _sync_unit_status(db: Session, unit: Unit) -> None:
    """
    Keep Unit.status consistent with whether it currently has an
    ACTIVE lease. A unit already flagged as under MAINTENANCE is left
    alone -- that's a manual manager decision, not derived from leases.
    """
    if unit.status == UnitStatus.MAINTENANCE:
        return

    has_active_lease = (
        db.query(Lease)
        .filter(Lease.unit_id == unit.id, Lease.status == LeaseStatus.ACTIVE)
        .first()
        is not None
    )

    unit.status = UnitStatus.OCCUPIED if has_active_lease else UnitStatus.AVAILABLE


@router.post("", response_model=LeaseResponse, status_code=status.HTTP_201_CREATED)
def create_lease(
    lease_data: LeaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.PROPERTY_MANAGER)),
):
    if lease_data.end_date is not None and lease_data.end_date <= lease_data.start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")

    tenant = db.query(User).filter(User.id == lease_data.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    if tenant.role != UserRole.TENANT:
        raise HTTPException(status_code=400, detail="User is not a tenant")

    unit = db.query(Unit).filter(Unit.id == lease_data.unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    ensure_property_access(unit.property, current_user)

    # Core business rule: no overlapping ACTIVE leases on the same unit.
    check_lease_overlap(
        db=db,
        unit_id=lease_data.unit_id,
        start_date=lease_data.start_date,
        end_date=lease_data.end_date,
    )

    new_lease = Lease(
        tenant_id=lease_data.tenant_id,
        unit_id=lease_data.unit_id,
        start_date=lease_data.start_date,
        end_date=lease_data.end_date,
        monthly_rent=lease_data.monthly_rent,
        security_deposit=lease_data.security_deposit,
        status=LeaseStatus.ACTIVE,
    )

    db.add(new_lease)
    db.flush()  # make the new lease visible to the status-sync query below (session has autoflush=False)
    _sync_unit_status(db, unit)
    db.commit()
    db.refresh(new_lease)

    return new_lease


@router.get("", response_model=list[LeaseResponse])
def get_leases(
    status_filter: LeaseStatus | None = Query(None, alias="status"),
    unit_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Lease).join(Unit)

    if current_user.role == UserRole.TENANT:
        query = query.filter(Lease.tenant_id == current_user.id)
    elif current_user.role == UserRole.PROPERTY_MANAGER:
        from app.models import Property
        query = query.join(Property, Unit.property_id == Property.id).filter(
            Property.manager_id == current_user.id
        )
    # ADMIN: no extra filter

    if status_filter is not None:
        query = query.filter(Lease.status == status_filter)

    if unit_id is not None:
        query = query.filter(Lease.unit_id == unit_id)

    return query.offset((page - 1) * page_size).limit(page_size).all()


@router.get("/{lease_id}", response_model=LeaseResponse)
def get_lease(
    lease_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lease = db.query(Lease).filter(Lease.id == lease_id).first()
    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")

    ensure_lease_view_access(lease, current_user)

    return lease


@router.put("/{lease_id}", response_model=LeaseResponse)
def update_lease(
    lease_id: int,
    lease_data: LeaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.PROPERTY_MANAGER)),
):
    lease = db.query(Lease).filter(Lease.id == lease_id).first()
    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")

    ensure_lease_manage_access(lease, current_user)

    if lease_data.end_date is not None and lease_data.end_date <= lease_data.start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")

    if lease_data.status == LeaseStatus.ACTIVE:
        check_lease_overlap(
            db=db,
            unit_id=lease.unit_id,
            start_date=lease_data.start_date,
            end_date=lease_data.end_date,
            exclude_lease_id=lease_id,
        )

    lease.start_date = lease_data.start_date
    lease.end_date = lease_data.end_date
    lease.monthly_rent = lease_data.monthly_rent
    lease.security_deposit = lease_data.security_deposit
    lease.status = lease_data.status

    db.flush()
    _sync_unit_status(db, lease.unit)
    db.commit()
    db.refresh(lease)

    return lease


@router.delete("/{lease_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lease(
    lease_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.PROPERTY_MANAGER)),
):
    lease = db.query(Lease).filter(Lease.id == lease_id).first()
    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")

    ensure_lease_manage_access(lease, current_user)

    unit = lease.unit
    db.delete(lease)
    db.flush()
    _sync_unit_status(db, unit)
    db.commit()

    return None
