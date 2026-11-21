from tests.conftest import auth_headers, DEMO_PASSWORD


def test_login_succeeds_with_correct_credentials(client, tenant_user):
    response = client.post(
        "/login",
        data={"username": tenant_user.email, "password": DEMO_PASSWORD},
    )

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["role"] == "TENANT"


def test_login_fails_with_wrong_password(client, tenant_user):
    response = client.post(
        "/login",
        data={"username": tenant_user.email, "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_login_fails_for_unknown_email(client):
    response = client.post(
        "/login",
        data={"username": "nobody@test.com", "password": "whatever"},
    )

    assert response.status_code == 401


def test_protected_endpoint_rejects_missing_token(client):
    response = client.get("/properties")
    assert response.status_code == 401


def test_protected_endpoint_rejects_garbage_token(client):
    response = client.get("/properties", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_get_me_returns_current_user(client, tenant_user):
    headers = auth_headers(client, tenant_user.email)
    response = client.get("/users/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["email"] == tenant_user.email
