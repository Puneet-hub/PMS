from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Lease, LeaseStatus


def check_lease_overlap(
    db: Session,
    unit_id: int,
    start_date: date,
    end_date: date | None,
    exclude_lease_id: int | None = None,
) -> None:
    """
    Enforce: a unit cannot have two overlapping ACTIVE leases.

    Only ACTIVE leases are checked -- a TERMINATED or EXPIRED lease
    should never block a new one from being created for the same
    date range, even if the dates on paper overlap.

    A lease with end_date=None is treated as open-ended / ongoing,
    meaning every later start_date is considered a conflict.

    Standard interval overlap check for two closed ranges:
        new_start < existing_end AND new_end > existing_start
    """

    query = db.query(Lease).filter(
        Lease.unit_id == unit_id,
        Lease.status == LeaseStatus.ACTIVE,
    )

    if exclude_lease_id is not None:
        query = query.filter(Lease.id != exclude_lease_id)

    for existing in query.all():
        existing_end = existing.end_date

        if existing_end is None:
            # Existing lease is open-ended -> any later start conflicts.
            if end_date is None or start_date >= existing.start_date:
                raise HTTPException(
                    status_code=409,
                    detail="Unit already has an overlapping active lease",
                )
            continue

        if end_date is None:
            # New lease is open-ended -> conflicts if it starts before
            # the existing lease ends.
            if start_date < existing_end:
                raise HTTPException(
                    status_code=409,
                    detail="Unit already has an overlapping active lease",
                )
            continue

        if start_date < existing_end and end_date > existing.start_date:
            raise HTTPException(
                status_code=409,
                detail="Unit already has an overlapping active lease",
            )
