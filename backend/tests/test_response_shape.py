"""
Regression tests: the frontend renders `unit.property.title` on lease and
maintenance screens, so those responses must embed the property.
"""
from tests.conftest import auth_headers
from tests.test_maintenance import make_leased_unit


def test_lease_response_includes_unit_property(client, db, manager_user, tenant_user):
    _, prop = make_leased_unit(db, manager_user, tenant_user)
    headers = auth_headers(client, manager_user.email)

    response = client.get("/leases", headers=headers)

    assert response.status_code == 200
    lease = response.json()[0]
    assert lease["unit"]["property"]["id"] == prop.id
    assert lease["unit"]["property"]["title"] == prop.title


def test_maintenance_response_includes_unit_property(client, db, manager_user, tenant_user):
    unit, prop = make_leased_unit(db, manager_user, tenant_user)
    headers = auth_headers(client, tenant_user.email)

    created = client.post(
        "/maintenance-requests",
        json={"unit_id": unit.id, "title": "Leak", "description": "Sink leaks", "priority": "HIGH"},
        headers=headers,
    )
    assert created.status_code == 201
    assert created.json()["unit"]["property"]["title"] == prop.title

    listed = client.get("/maintenance-requests", headers=headers).json()
    assert listed[0]["unit"]["property"]["title"] == prop.title
