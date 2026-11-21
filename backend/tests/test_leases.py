from datetime import date, timedelta

from app.models import Property, Unit, UnitStatus, Lease, LeaseStatus
from tests.conftest import auth_headers


def make_unit(db, manager, unit_number="101"):
    prop = Property(title="Lease Test Property", address="1 Test St", manager_id=manager.id)
    db.add(prop)
    db.commit()
    db.refresh(prop)

    unit = Unit(
        property_id=prop.id, unit_number=unit_number, bedrooms=1, bathrooms=1,
        monthly_rent=15000, status=UnitStatus.AVAILABLE,
    )
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit, prop


def create_lease_payload(tenant_id, unit_id, start, end):
    return {
        "tenant_id": tenant_id,
        "unit_id": unit_id,
        "start_date": start.isoformat(),
        "end_date": end.isoformat() if end else None,
        "monthly_rent": 15000,
        "security_deposit": 30000,
    }


def test_overlapping_active_lease_is_rejected(client, db, manager_user, tenant_user, other_tenant_user):
    unit, _ = make_unit(db, manager_user)
    headers = auth_headers(client, manager_user.email)

    # Unit A leased Jan 1 - Dec 31
    first = client.post(
        "/leases",
        json=create_lease_payload(
            tenant_user.id, unit.id,
            date(2027, 1, 1), date(2027, 12, 31),
        ),
        headers=headers,
    )
    assert first.status_code == 201

    # Overlapping lease for a different tenant on the same unit -> rejected
    second = client.post(
        "/leases",
        json=create_lease_payload(
            other_tenant_user.id, unit.id,
            date(2027, 6, 1), date(2028, 6, 1),
        ),
        headers=headers,
    )

    assert second.status_code == 409


def test_non_overlapping_lease_after_previous_ends_is_accepted(client, db, manager_user, tenant_user, other_tenant_user):
    unit, _ = make_unit(db, manager_user)
    headers = auth_headers(client, manager_user.email)

    first = client.post(
        "/leases",
        json=create_lease_payload(tenant_user.id, unit.id, date(2027, 1, 1), date(2027, 6, 30)),
        headers=headers,
    )
    assert first.status_code == 201

    second = client.post(
        "/leases",
        json=create_lease_payload(other_tenant_user.id, unit.id, date(2027, 7, 1), date(2027, 12, 31)),
        headers=headers,
    )

    assert second.status_code == 201


def test_terminated_lease_does_not_block_new_overlapping_lease(client, db, manager_user, tenant_user, other_tenant_user):
    unit, _ = make_unit(db, manager_user)
    headers = auth_headers(client, manager_user.email)

    first = client.post(
        "/leases",
        json=create_lease_payload(tenant_user.id, unit.id, date(2027, 1, 1), date(2027, 12, 31)),
        headers=headers,
    )
    assert first.status_code == 201
    first_id = first.json()["id"]

    terminate = client.put(
        f"/leases/{first_id}",
        json={
            "start_date": "2027-01-01",
            "end_date": "2027-12-31",
            "monthly_rent": 15000,
            "security_deposit": 30000,
            "status": "TERMINATED",
        },
        headers=headers,
    )
    assert terminate.status_code == 200

    second = client.post(
        "/leases",
        json=create_lease_payload(other_tenant_user.id, unit.id, date(2027, 3, 1), date(2027, 9, 1)),
        headers=headers,
    )

    assert second.status_code == 201


def test_lease_with_end_date_before_start_date_is_rejected(client, db, manager_user, tenant_user):
    unit, _ = make_unit(db, manager_user)
    headers = auth_headers(client, manager_user.email)

    response = client.post(
        "/leases",
        json=create_lease_payload(tenant_user.id, unit.id, date(2027, 6, 1), date(2027, 1, 1)),
        headers=headers,
    )

    assert response.status_code == 400


def test_creating_lease_marks_unit_occupied(client, db, manager_user, tenant_user):
    unit, _ = make_unit(db, manager_user)
    headers = auth_headers(client, manager_user.email)

    response = client.post(
        "/leases",
        json=create_lease_payload(tenant_user.id, unit.id, date.today(), date.today() + timedelta(days=180)),
        headers=headers,
    )
    assert response.status_code == 201

    unit_response = client.get(f"/units/{unit.id}", headers=headers)
    assert unit_response.json()["status"] == "OCCUPIED"


def test_manager_cannot_create_lease_for_unit_they_dont_manage(client, db, manager_user, other_manager_user, tenant_user):
    unit, _ = make_unit(db, other_manager_user)
    headers = auth_headers(client, manager_user.email)

    response = client.post(
        "/leases",
        json=create_lease_payload(tenant_user.id, unit.id, date.today(), date.today() + timedelta(days=180)),
        headers=headers,
    )

    assert response.status_code == 403
