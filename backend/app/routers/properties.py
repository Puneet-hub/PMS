from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole, Property, Unit
from app.permissions import ensure_property_access
from app.schemas import PropertyCreate, PropertyResponse, PropertyWithStatsResponse
from app.security import get_current_user, require_role

router = APIRouter(prefix="/properties", tags=["properties"])


def _with_stats(db: Session, prop: Property) -> dict:
    units = db.query(Unit).filter(Unit.property_id == prop.id).all()
    occupied = sum(1 for u in units if u.status.value == "OCCUPIED")
    return {
        "id": prop.id,
        "title": prop.title,
        "address": prop.address,
        "manager_id": prop.manager_id,
        "total_units": len(units),
        "occupied_units": occupied,
        "available_units": len(units) - occupied,
    }


@router.post("", response_model=PropertyResponse, status_code=status.HTTP_201_CREATED)
def create_property(
    property_data: PropertyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.PROPERTY_MANAGER)),
):
    new_property = Property(
        title=property_data.title,
        address=property_data.address,
        manager_id=current_user.id,
    )

    db.add(new_property)
    db.commit()
    db.refresh(new_property)

    return new_property


@router.get("", response_model=list[PropertyWithStatsResponse])
def get_properties(
    search: str | None = Query(None, description="Search by title or address"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Property)

    if current_user.role == UserRole.PROPERTY_MANAGER:
        query = query.filter(Property.manager_id == current_user.id)
    elif current_user.role == UserRole.TENANT:
        # A tenant only ever needs to see the property tied to their unit,
        # exposed via /users/me/lease instead. Block the general listing.
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if search:
        like = f"%{search}%"
        query = query.filter(or_(Property.title.ilike(like), Property.address.ilike(like)))

    properties = query.offset((page - 1) * page_size).limit(page_size).all()

    return [_with_stats(db, p) for p in properties]


@router.get("/{property_id}", response_model=PropertyWithStatsResponse)
def get_property(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    property_obj = db.query(Property).filter(Property.id == property_id).first()
    if not property_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    if current_user.role != UserRole.TENANT:
        ensure_property_access(property_obj, current_user)

    return _with_stats(db, property_obj)


@router.put("/{property_id}", response_model=PropertyResponse)
def update_property(
    property_id: int,
    property_data: PropertyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.PROPERTY_MANAGER)),
):
    property_obj = db.query(Property).filter(Property.id == property_id).first()
    if not property_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    ensure_property_access(property_obj, current_user)

    property_obj.title = property_data.title
    property_obj.address = property_data.address

    db.commit()
    db.refresh(property_obj)

    return property_obj


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_property(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.PROPERTY_MANAGER)),
):
    property_obj = db.query(Property).filter(Property.id == property_id).first()
    if not property_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    ensure_property_access(property_obj, current_user)

    db.delete(property_obj)
    db.commit()

    return None
