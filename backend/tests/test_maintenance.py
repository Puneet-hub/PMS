from datetime import date, timedelta

from app.models import Property, Unit, UnitStatus, Lease, LeaseStatus
from tests.conftest import auth_headers


def make_leased_unit(db, manager, tenant, unit_number="101"):
    prop = Property(title="Maintenance Test Property", address="1 Test St", manager_id=manager.id)
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

    lease = Lease(
        tenant_id=tenant.id, unit_id=unit.id,
        start_date=date.today() - timedelta(days=10),
        end_date=date.today() + timedelta(days=355),
        monthly_rent=15000, security_deposit=30000,
        status=LeaseStatus.ACTIVE,
    )
    db.add(lease)
    db.commit()

    return unit, prop


def test_tenant_can_create_maintenance_request_for_own_unit(client, db, manager_user, tenant_user):
    unit, _ = make_leased_unit(db, manager_user, tenant_user)
    headers = auth_headers(client, tenant_user.email)

    response = client.post(
        "/maintenance-requests",
        json={
            "unit_id": unit.id,
            "title": "Broken heater",
            "description": "Heater does not turn on at all.",
            "priority": "HIGH",
        },
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["status"] == "OPEN"


def test_tenant_cannot_create_maintenance_request_for_unleased_unit(client, db, manager_user, tenant_user):
    # Unit exists but this tenant has no lease on it.
    prop = Property(title="Other Property", address="2 Test St", manager_id=manager_user.id)
    db.add(prop)
    db.commit()
    db.refresh(prop)

    unit = Unit(
        property_id=prop.id, unit_number="999", bedrooms=1, bathrooms=1,
        monthly_rent=10000, status=UnitStatus.AVAILABLE,
    )
    db.add(unit)
    db.commit()
    db.refresh(unit)

    headers = auth_headers(client, tenant_user.email)
    response = client.post(
        "/maintenance-requests",
        json={"unit_id": unit.id, "title": "Fake request", "description": "I don't live here"},
        headers=headers,
    )

    assert response.status_code == 403


def test_manager_can_create_maintenance_request_is_rejected(client, db, manager_user, tenant_user):
    """Only tenants file requests -- a manager posting one should be rejected."""
    unit, _ = make_leased_unit(db, manager_user, tenant_user)
    headers = auth_headers(client, manager_user.email)

    response = client.post(
        "/maintenance-requests",
        json={"unit_id": unit.id, "title": "Manager filing", "description": "Should not be allowed"},
        headers=headers,
    )

    assert response.status_code == 403


def test_tenant_cannot_change_maintenance_status(client, db, manager_user, tenant_user):
    unit, _ = make_leased_unit(db, manager_user, tenant_user)
    tenant_headers = auth_headers(client, tenant_user.email)

    created = client.post(
        "/maintenance-requests",
        json={"unit_id": unit.id, "title": "Leaky pipe", "description": "Under the sink"},
        headers=tenant_headers,
    )
    request_id = created.json()["id"]

    response = client.patch(
        f"/maintenance-requests/{request_id}",
        json={"status": "RESOLVED"},
        headers=tenant_headers,
    )

    assert response.status_code == 403


def test_manager_can_assign_and_change_status(client, db, manager_user, tenant_user):
    unit, _ = make_leased_unit(db, manager_user, tenant_user)
    tenant_headers = auth_headers(client, tenant_user.email)
    manager_headers = auth_headers(client, manager_user.email)

    created = client.post(
        "/maintenance-requests",
        json={"unit_id": unit.id, "title": "Leaky pipe", "description": "Under the sink"},
        headers=tenant_headers,
    )
    request_id = created.json()["id"]

    response = client.patch(
        f"/maintenance-requests/{request_id}",
        json={"status": "IN_PROGRESS", "assigned_manager_id": manager_user.id},
        headers=manager_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "IN_PROGRESS"
    assert body["assigned_manager_id"] == manager_user.id


def test_closed_request_cannot_be_reopened(client, db, manager_user, tenant_user):
    unit, _ = make_leased_unit(db, manager_user, tenant_user)
    tenant_headers = auth_headers(client, tenant_user.email)
    manager_headers = auth_headers(client, manager_user.email)

    created = client.post(
        "/maintenance-requests",
        json={"unit_id": unit.id, "title": "Leaky pipe", "description": "Under the sink"},
        headers=tenant_headers,
    )
    request_id = created.json()["id"]

    close_response = client.patch(
        f"/maintenance-requests/{request_id}",
        json={"status": "CLOSED"},
        headers=manager_headers,
    )
    assert close_response.status_code == 200

    reopen_response = client.patch(
        f"/maintenance-requests/{request_id}",
        json={"status": "OPEN"},
        headers=manager_headers,
    )
    assert reopen_response.status_code == 400
