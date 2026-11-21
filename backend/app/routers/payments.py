from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole, Lease, Payment, PaymentStatus, Unit, Property
from app.permissions import ensure_lease_manage_access, ensure_lease_view_access
from app.schemas import PaymentCreate, PaymentUpdate, PaymentResponse
from app.security import get_current_user, require_role

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.PROPERTY_MANAGER)),
):
    lease = db.query(Lease).filter(Lease.id == payment_data.lease_id).first()
    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")

    ensure_lease_manage_access(lease, current_user)

    new_payment = Payment(
        lease_id=payment_data.lease_id,
        amount=payment_data.amount,
        due_date=payment_data.due_date,
        status=payment_data.status,
    )

    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)

    return new_payment


@router.get("", response_model=list[PaymentResponse])
def get_payments(
    status_filter: PaymentStatus | None = Query(None, alias="status"),
    lease_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Payment).join(Lease)

    if current_user.role == UserRole.TENANT:
        query = query.filter(Lease.tenant_id == current_user.id)
    elif current_user.role == UserRole.PROPERTY_MANAGER:
        query = (
            query.join(Unit, Lease.unit_id == Unit.id)
            .join(Property, Unit.property_id == Property.id)
            .filter(Property.manager_id == current_user.id)
        )

    if status_filter is not None:
        query = query.filter(Payment.status == status_filter)

    if lease_id is not None:
        query = query.filter(Payment.lease_id == lease_id)

    return query.offset((page - 1) * page_size).limit(page_size).all()


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    ensure_lease_view_access(payment.lease, current_user)

    return payment


@router.put("/{payment_id}", response_model=PaymentResponse)
def update_payment(
    payment_id: int,
    payment_data: PaymentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.PROPERTY_MANAGER)),
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    ensure_lease_manage_access(payment.lease, current_user)

    if payment_data.status == PaymentStatus.PAID and payment_data.paid_date is None:
        raise HTTPException(status_code=400, detail="paid_date is required when marking a payment as PAID")

    payment.amount = payment_data.amount
    payment.due_date = payment_data.due_date
    payment.paid_date = payment_data.paid_date
    payment.status = payment_data.status

    db.commit()
    db.refresh(payment)

    return payment


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.PROPERTY_MANAGER)),
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    ensure_lease_manage_access(payment.lease, current_user)

    db.delete(payment)
    db.commit()

    return None
