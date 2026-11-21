from app.models import Property, Unit, UnitStatus
from tests.conftest import auth_headers


def make_property(db, manager, title="Test Property"):
    prop = Property(title=title, address="1 Test St", manager_id=manager.id)
    db.add(prop)
    db.commit()
    db.refresh(prop)
    return prop


def make_unit(db, prop, unit_number="101"):
    unit = Unit(
        property_id=prop.id,
        unit_number=unit_number,
        bedrooms=2,
        bathrooms=1,
        monthly_rent=20000,
        status=UnitStatus.AVAILABLE,
    )
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit


def test_tenant_cannot_list_properties(client, db, tenant_user, manager_user):
    make_property(db, manager_user)
    headers = auth_headers(client, tenant_user.email)

    response = client.get("/properties", headers=headers)

    assert response.status_code == 403


def test_tenant_cannot_create_property(client, tenant_user):
    headers = auth_headers(client, tenant_user.email)

    response = client.post(
        "/properties",
        json={"title": "Hack House", "address": "1 Nowhere"},
        headers=headers,
    )

    assert response.status_code == 403


def test_manager_can_only_see_own_properties(client, db, manager_user, other_manager_user):
    make_property(db, manager_user, title="Mine")
    make_property(db, other_manager_user, title="Theirs")

    headers = auth_headers(client, manager_user.email)
    response = client.get("/properties", headers=headers)

    assert response.status_code == 200
    titles = [p["title"] for p in response.json()]
    assert "Mine" in titles
    assert "Theirs" not in titles


def test_manager_cannot_update_another_managers_property(client, db, manager_user, other_manager_user):
    other_prop = make_property(db, other_manager_user, title="Not Yours")
    headers = auth_headers(client, manager_user.email)

    response = client.put(
        f"/properties/{other_prop.id}",
        json={"title": "Hijacked", "address": "New address"},
        headers=headers,
    )

    assert response.status_code == 403


def test_admin_can_access_any_property(client, db, admin_user, manager_user):
    prop = make_property(db, manager_user)
    headers = auth_headers(client, admin_user.email)

    response = client.get(f"/properties/{prop.id}", headers=headers)

    assert response.status_code == 200


def test_property_manager_can_only_create_tenant_accounts(client, manager_user):
    headers = auth_headers(client, manager_user.email)

    # Trying to create another PROPERTY_MANAGER should be forbidden.
    response = client.post(
        "/users",
        json={
            "name": "Sneaky",
            "email": "sneaky@test.com",
            "role": "PROPERTY_MANAGER",
            "password": "whatever123",
        },
        headers=headers,
    )
    assert response.status_code == 403

    # Creating a TENANT is allowed.
    response = client.post(
        "/users",
        json={
            "name": "New Tenant",
            "email": "newtenant@test.com",
            "role": "TENANT",
            "password": "whatever123",
        },
        headers=headers,
    )
    assert response.status_code == 201
