from datetime import date, timedelta

from app.models import Property, Unit, UnitStatus, Lease, LeaseStatus, MaintenanceRequest, MaintenanceStatus, MaintenancePriority
from tests.conftest import auth_headers


def make_unit(db, manager, unit_number="101"):
    prop = Property(title="Isolation Test Property", address="1 Test St", manager_id=manager.id)
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
    return unit


def make_lease(db, tenant, unit):
    lease = Lease(
        tenant_id=tenant.id, unit_id=unit.id,
        start_date=date.today() - timedelta(days=30),
        end_date=date.today() + timedelta(days=335),
        monthly_rent=15000, security_deposit=30000,
        status=LeaseStatus.ACTIVE,
    )
    db.add(lease)
    db.commit()
    db.refresh(lease)
    return lease


def test_tenant_cannot_view_another_tenants_lease(client, db, manager_user, tenant_user, other_tenant_user):
    unit = make_unit(db, manager_user)
    lease = make_lease(db, tenant_user, unit)

    headers = auth_headers(client, other_tenant_user.email)
    response = client.get(f"/leases/{lease.id}", headers=headers)

    assert response.status_code == 403


def test_tenant_lease_list_only_shows_own_leases(client, db, manager_user, tenant_user, other_tenant_user):
    unit1 = make_unit(db, manager_user, unit_number="101")
    unit2 = make_unit(db, manager_user, unit_number="102")
    make_lease(db, tenant_user, unit1)
    make_lease(db, other_tenant_user, unit2)

    headers = auth_headers(client, tenant_user.email)
    response = client.get("/leases", headers=headers)

    assert response.status_code == 200
    tenant_ids = {lease["tenant_id"] for lease in response.json()}
    assert tenant_ids == {tenant_user.id}


def test_tenant_cannot_view_another_tenants_maintenance_request(client, db, manager_user, tenant_user, other_tenant_user):
    unit = make_unit(db, manager_user)
    make_lease(db, tenant_user, unit)

    request_obj = MaintenanceRequest(
        unit_id=unit.id, created_by_id=tenant_user.id,
        title="Broken window", description="Cracked glass in bedroom window",
        priority=MaintenancePriority.MEDIUM, status=MaintenanceStatus.OPEN,
    )
    db.add(request_obj)
    db.commit()
    db.refresh(request_obj)

    headers = auth_headers(client, other_tenant_user.email)
    response = client.get(f"/maintenance-requests/{request_obj.id}", headers=headers)

    assert response.status_code == 403


def test_tenant_cannot_comment_on_another_tenants_request(client, db, manager_user, tenant_user, other_tenant_user):
    unit = make_unit(db, manager_user)
    make_lease(db, tenant_user, unit)

    request_obj = MaintenanceRequest(
        unit_id=unit.id, created_by_id=tenant_user.id,
        title="Broken window", description="Cracked glass in bedroom window",
        priority=MaintenancePriority.MEDIUM, status=MaintenanceStatus.OPEN,
    )
    db.add(request_obj)
    db.commit()
    db.refresh(request_obj)

    headers = auth_headers(client, other_tenant_user.email)
    response = client.post(
        f"/maintenance-requests/{request_obj.id}/comments",
        json={"content": "Not my request but let me comment anyway"},
        headers=headers,
    )

    assert response.status_code == 403
