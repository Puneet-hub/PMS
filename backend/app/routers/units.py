from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole, Property, Unit, UnitStatus
from app.permissions import ensure_property_access, ensure_unit_write_access
from app.schemas import UnitCreate, UnitUpdate, UnitResponse, UnitWithPropertyResponse
from app.security import get_current_user, require_role

router = APIRouter(prefix="/units", tags=["units"])


@router.post("", response_model=UnitResponse, status_code=status.HTTP_201_CREATED)
def create_unit(
    unit_data: UnitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.PROPERTY_MANAGER)),
):
    property_obj = db.query(Property).filter(Property.id == unit_data.property_id).first()
    if not property_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    ensure_property_access(property_obj, current_user)

    duplicate = db.query(Unit).filter(
        Unit.property_id == unit_data.property_id,
        Unit.unit_number == unit_data.unit_number,
    ).first()
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This property already has a unit with that number",
        )

    new_unit = Unit(**unit_data.model_dump())

    db.add(new_unit)
    db.commit()
    db.refresh(new_unit)

    return new_unit


@router.get("", response_model=list[UnitWithPropertyResponse])
def get_units(
    property_id: int | None = None,
    status_filter: UnitStatus | None = Query(None, alias="status"),
    search: str | None = Query(None, description="Search by unit number"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Unit).join(Property)

    if current_user.role == UserRole.PROPERTY_MANAGER:
        query = query.filter(Property.manager_id == current_user.id)
    elif current_user.role == UserRole.TENANT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if property_id is not None:
        query = query.filter(Unit.property_id == property_id)

    if status_filter is not None:
        query = query.filter(Unit.status == status_filter)

    if search:
        query = query.filter(Unit.unit_number.ilike(f"%{search}%"))

    return query.offset((page - 1) * page_size).limit(page_size).all()


@router.get("/{unit_id}", response_model=UnitWithPropertyResponse)
def get_unit(
    unit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")

    if current_user.role != UserRole.TENANT:
        ensure_property_access(unit.property, current_user)

    return unit


@router.put("/{unit_id}", response_model=UnitResponse)
def update_unit(
    unit_id: int,
    unit_data: UnitUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.PROPERTY_MANAGER)),
):
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")

    ensure_unit_write_access(unit, current_user)

    for field, value in unit_data.model_dump().items():
        setattr(unit, field, value)

    db.commit()
    db.refresh(unit)

    return unit


@router.delete("/{unit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_unit(
    unit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.PROPERTY_MANAGER)),
):
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")

    ensure_unit_write_access(unit, current_user)

    db.delete(unit)
    db.commit()

    return None
