from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    User,
    UserRole,
    Unit,
    Property,
    Lease,
    LeaseStatus,
    MaintenanceRequest,
    MaintenancePriority,
    MaintenanceStatus,
    MaintenanceComment,
)
from app.permissions import ensure_maintenance_view_access, ensure_property_access
from app.schemas import (
    MaintenanceRequestCreate,
    MaintenanceRequestUpdate,
    MaintenanceRequestResponse,
    MaintenanceCommentCreate,
    MaintenanceCommentResponse,
)
from app.security import get_current_user, require_role

router = APIRouter(prefix="/maintenance-requests", tags=["maintenance"])


@router.post("", response_model=MaintenanceRequestResponse, status_code=status.HTTP_201_CREATED)
def create_maintenance_request(
    request_data: MaintenanceRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.TENANT)),
):
    unit = db.query(Unit).filter(Unit.id == request_data.unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    # A tenant can only file requests for a unit they actually have an
    # active lease on -- prevents filing requests for arbitrary units.
    has_lease = (
        db.query(Lease)
        .filter(
            Lease.unit_id == request_data.unit_id,
            Lease.tenant_id == current_user.id,
            Lease.status == LeaseStatus.ACTIVE,
        )
        .first()
    )
    if not has_lease:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create maintenance requests for a unit you currently lease",
        )

    new_request = MaintenanceRequest(
        unit_id=request_data.unit_id,
        created_by_id=current_user.id,
        title=request_data.title,
        description=request_data.description,
        priority=request_data.priority,
        status=MaintenanceStatus.OPEN,
    )

    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    return new_request


@router.get("", response_model=list[MaintenanceRequestResponse])
def get_maintenance_requests(
    status_filter: MaintenanceStatus | None = Query(None, alias="status"),
    priority: MaintenancePriority | None = None,
    unit_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(MaintenanceRequest).join(Unit)

    if current_user.role == UserRole.TENANT:
        query = query.filter(MaintenanceRequest.created_by_id == current_user.id)
    elif current_user.role == UserRole.PROPERTY_MANAGER:
        query = query.join(Property, Unit.property_id == Property.id).filter(
            Property.manager_id == current_user.id
        )

    if status_filter is not None:
        query = query.filter(MaintenanceRequest.status == status_filter)

    if priority is not None:
        query = query.filter(MaintenanceRequest.priority == priority)

    if unit_id is not None:
        query = query.filter(MaintenanceRequest.unit_id == unit_id)

    return (
        query.order_by(MaintenanceRequest.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )


@router.get("/{request_id}", response_model=MaintenanceRequestResponse)
def get_maintenance_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    request_obj = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
    if not request_obj:
        raise HTTPException(status_code=404, detail="Maintenance request not found")

    ensure_maintenance_view_access(request_obj, current_user)

    return request_obj


@router.patch("/{request_id}", response_model=MaintenanceRequestResponse)
def update_maintenance_request(
    request_id: int,
    update_data: MaintenanceRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.PROPERTY_MANAGER)),
):
    """
    Only Admin/Property Manager can assign a request or change its
    status/priority -- tenants can view and comment, but not steer the
    workflow. Enforced here via require_role, not just in the frontend.
    """
    request_obj = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
    if not request_obj:
        raise HTTPException(status_code=404, detail="Maintenance request not found")

    ensure_property_access(request_obj.unit.property, current_user)

    if update_data.assigned_manager_id is not None:
        manager = db.query(User).filter(User.id == update_data.assigned_manager_id).first()
        if not manager or manager.role not in (UserRole.ADMIN, UserRole.PROPERTY_MANAGER):
            raise HTTPException(status_code=400, detail="assigned_manager_id must be a manager or admin")
        request_obj.assigned_manager_id = update_data.assigned_manager_id

    if update_data.status is not None:
        # Reasonable status-flow validation: can't reopen a closed request
        # by skipping straight back to OPEN once it's CLOSED.
        if request_obj.status == MaintenanceStatus.CLOSED and update_data.status != MaintenanceStatus.CLOSED:
            raise HTTPException(status_code=400, detail="A closed request cannot be reopened")
        request_obj.status = update_data.status

    if update_data.priority is not None:
        request_obj.priority = update_data.priority

    db.commit()
    db.refresh(request_obj)

    return request_obj


@router.post(
    "/{request_id}/comments",
    response_model=MaintenanceCommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_comment(
    request_id: int,
    comment_data: MaintenanceCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    request_obj = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
    if not request_obj:
        raise HTTPException(status_code=404, detail="Maintenance request not found")

    ensure_maintenance_view_access(request_obj, current_user)

    new_comment = MaintenanceComment(
        maintenance_request_id=request_id,
        author_id=current_user.id,
        content=comment_data.content,
    )

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return new_comment
