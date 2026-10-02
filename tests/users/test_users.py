import pytest
from fastapi.testclient import TestClient


# ============================================================
# GET /users
# ============================================================


def test_list_users_as_admin(
    client: TestClient,
    create_user,
    get_token,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
        full_name="Admin User",
    )

    user1 = create_user(
        email="user1@example.com",
        role="member",
        full_name="User One",
    )

    user2 = create_user(
        email="user2@example.com",
        role="manager",
        full_name="User Two",
    )

    token = get_token(admin.email)

    response = client.get(
        "/users",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 3

    assert data[0]["id"] == admin.id
    assert data[1]["id"] == user1.id
    assert data[2]["id"] == user2.id

    for user in data:
        assert "id" in user
        assert "email" in user
        assert "full_name" in user
        assert "role" in user
        assert "is_active" in user
        assert "created_at" in user
        assert "password_hash" not in user


def test_list_users_requires_authentication(
    client: TestClient,
):
    response = client.get("/users")

    assert response.status_code == 401


def test_list_users_member_forbidden(
    client: TestClient,
    create_user,
    get_token,
):
    member = create_user(
        email="member@example.com",
        role="member",
    )

    token = get_token(member.email)

    response = client.get(
        "/users",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_list_users_manager_forbidden(
    client: TestClient,
    create_user,
    get_token,
):
    manager = create_user(
        email="manager@example.com",
        role="manager",
    )

    token = get_token(manager.email)

    response = client.get(
        "/users",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_list_users_invalid_token(
    client: TestClient,
):
    response = client.get(
        "/users",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401


def test_list_users_pagination(
    client: TestClient,
    create_user,
    get_token,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
    )

    create_user(email="user1@example.com")
    create_user(email="user2@example.com")
    create_user(email="user3@example.com")
    create_user(email="user4@example.com")

    token = get_token(admin.email)

    response = client.get(
        "/users?page=1&page_size=2",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2


def test_list_users_second_page(
    client: TestClient,
    create_user,
    get_token,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
    )

    create_user(email="user1@example.com")
    create_user(email="user2@example.com")
    create_user(email="user3@example.com")
    create_user(email="user4@example.com")

    token = get_token(admin.email)

    response = client.get(
        "/users?page=2&page_size=2",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2


@pytest.mark.parametrize(
    "query",
    [
        "?page=0",
        "?page=-1",
        "?page_size=0",
        "?page_size=-1",
        "?page_size=101",
    ],
)
def test_list_users_invalid_pagination(
    client: TestClient,
    create_user,
    get_token,
    query,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
    )

    token = get_token(admin.email)

    response = client.get(
        f"/users{query}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


def test_list_users_empty(
    client: TestClient,
    create_user,
    get_token,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
    )

    token = get_token(admin.email)

    response = client.get(
        "/users",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["email"] == admin.email


# ============================================================
# GET /users/{user_id}
# ============================================================


def test_get_user_as_admin(
    client: TestClient,
    create_user,
    get_token,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
    )

    user = create_user(
        email="user@example.com",
        role="member",
        full_name="Normal User",
    )

    token = get_token(admin.email)

    response = client.get(
        f"/users/{user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == user.id
    assert data["email"] == user.email
    assert data["full_name"] == "Normal User"
    assert data["role"] == "member"
    assert data["is_active"] is True
    assert "password_hash" not in data


def test_get_user_self_as_admin(
    client: TestClient,
    create_user,
    get_token,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
    )

    token = get_token(admin.email)

    response = client.get(
        f"/users/{admin.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == admin.id
    assert data["email"] == admin.email


def test_get_user_not_found(
    client: TestClient,
    create_user,
    get_token,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
    )

    token = get_token(admin.email)

    response = client.get(
        "/users/999999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_get_user_requires_authentication(
    client: TestClient,
    create_user,
):
    user = create_user(
        email="user@example.com",
    )

    response = client.get(f"/users/{user.id}")

    assert response.status_code == 401


def test_get_user_member_forbidden(
    client: TestClient,
    create_user,
    get_token,
):
    member = create_user(
        email="member@example.com",
        role="member",
    )

    target = create_user(
        email="target@example.com",
        role="member",
    )

    token = get_token(member.email)

    response = client.get(
        f"/users/{target.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_get_user_manager_forbidden(
    client: TestClient,
    create_user,
    get_token,
):
    manager = create_user(
        email="manager@example.com",
        role="manager",
    )

    target = create_user(
        email="target@example.com",
        role="member",
    )

    token = get_token(manager.email)

    response = client.get(
        f"/users/{target.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


@pytest.mark.parametrize(
    "user_id",
    [
        "abc",
        "1.5",
        "invalid",
    ],
)
def test_get_user_invalid_id(
    client: TestClient,
    create_user,
    get_token,
    user_id,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
    )

    token = get_token(admin.email)

    response = client.get(
        f"/users/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


# ============================================================
# PATCH /users/{user_id}/role
# ============================================================


@pytest.mark.parametrize(
    "new_role",
    [
        "admin",
        "manager",
        "member",
    ],
)
def test_update_user_role(
    client: TestClient,
    create_user,
    get_token,
    new_role,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
    )

    user = create_user(
        email="user@example.com",
        role="member",
    )

    token = get_token(admin.email)

    response = client.patch(
        f"/users/{user.id}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": new_role},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == user.id
    assert data["role"] == new_role


def test_update_user_role_persists(
    client: TestClient,
    create_user,
    get_token,
    db,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
    )

    user = create_user(
        email="user@example.com",
        role="member",
    )

    token = get_token(admin.email)

    response = client.patch(
        f"/users/{user.id}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "manager"},
    )

    assert response.status_code == 200

    db.refresh(user)

    assert user.role == "manager"


def test_admin_cannot_remove_own_admin_role(
    client: TestClient,
    create_user,
    get_token,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
    )

    token = get_token(admin.email)

    response = client.patch(
        f"/users/{admin.id}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "member"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "You cannot remove your own admin role"
    )


def test_admin_can_keep_own_admin_role(
    client: TestClient,
    create_user,
    get_token,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
    )

    token = get_token(admin.email)

    response = client.patch(
        f"/users/{admin.id}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "admin"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_update_user_role_not_found(
    client: TestClient,
    create_user,
    get_token,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
    )

    token = get_token(admin.email)

    response = client.patch(
        "/users/999999/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "member"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_update_user_role_requires_authentication(
    client: TestClient,
    create_user,
):
    user = create_user(
        email="user@example.com",
    )

    response = client.patch(
        f"/users/{user.id}/role",
        json={"role": "manager"},
    )

    assert response.status_code == 401


def test_update_user_role_member_forbidden(
    client: TestClient,
    create_user,
    get_token,
):
    member = create_user(
        email="member@example.com",
        role="member",
    )

    target = create_user(
        email="target@example.com",
        role="member",
    )

    token = get_token(member.email)

    response = client.patch(
        f"/users/{target.id}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "manager"},
    )

    assert response.status_code == 403


def test_update_user_role_manager_forbidden(
    client: TestClient,
    create_user,
    get_token,
):
    manager = create_user(
        email="manager@example.com",
        role="manager",
    )

    target = create_user(
        email="target@example.com",
        role="member",
    )

    token = get_token(manager.email)

    response = client.patch(
        f"/users/{target.id}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "admin"},
    )

    assert response.status_code == 403


@pytest.mark.parametrize(
    "role",
    [
        "owner",
        "superadmin",
        "ADMIN",
        "",
        None,
    ],
)
def test_update_user_role_invalid_role(
    client: TestClient,
    create_user,
    get_token,
    role,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
    )

    user = create_user(
        email="user@example.com",
        role="member",
    )

    token = get_token(admin.email)

    response = client.patch(
        f"/users/{user.id}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": role},
    )

    assert response.status_code == 422


def test_update_user_role_missing_role(
    client: TestClient,
    create_user,
    get_token,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
    )

    user = create_user(
        email="user@example.com",
        role="member",
    )

    token = get_token(admin.email)

    response = client.patch(
        f"/users/{user.id}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )

    assert response.status_code == 422


# ============================================================
# PATCH /users/{user_id}/status
# ============================================================


def test_deactivate_user(
    client: TestClient,
    create_user,
    get_token,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
    )

    user = create_user(
        email="user@example.com",
        role="member",
        is_active=True,
    )

    token = get_token(admin.email)

    response = client.patch(
        f"/users/{user.id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_active": False},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == user.id
    assert data["is_active"] is False


def test_activate_user(
    client: TestClient,
    create_user,
    get_token,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
    )

    user = create_user(
        email="user@example.com",
        role="member",
        is_active=False,
    )

    token = get_token(admin.email)

    response = client.patch(
        f"/users/{user.id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_active": True},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == user.id
    assert data["is_active"] is True


def test_update_user_status_persists(
    client: TestClient,
    create_user,
    get_token,
    db,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
    )

    user = create_user(
        email="user@example.com",
        role="member",
        is_active=True,
    )

    token = get_token(admin.email)

    response = client.patch(
        f"/users/{user.id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_active": False},
    )

    assert response.status_code == 200

    db.refresh(user)

    assert user.is_active is False


def test_admin_cannot_deactivate_own_account(
    client: TestClient,
    create_user,
    get_token,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
        is_active=True,
    )

    token = get_token(admin.email)

    response = client.patch(
        f"/users/{admin.id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_active": False},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "You cannot deactivate your own account"
    )


def test_admin_can_keep_own_account_active(
    client: TestClient,
    create_user,
    get_token,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
        is_active=True,
    )

    token = get_token(admin.email)

    response = client.patch(
        f"/users/{admin.id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_active": True},
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is True


def test_update_user_status_not_found(
    client: TestClient,
    create_user,
    get_token,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
    )

    token = get_token(admin.email)

    response = client.patch(
        "/users/999999/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_active": False},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_update_user_status_requires_authentication(
    client: TestClient,
    create_user,
):
    user = create_user(
        email="user@example.com",
    )

    response = client.patch(
        f"/users/{user.id}/status",
        json={"is_active": False},
    )

    assert response.status_code == 401


def test_update_user_status_member_forbidden(
    client: TestClient,
    create_user,
    get_token,
):
    member = create_user(
        email="member@example.com",
        role="member",
    )

    target = create_user(
        email="target@example.com",
        role="member",
    )

    token = get_token(member.email)

    response = client.patch(
        f"/users/{target.id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_active": False},
    )

    assert response.status_code == 403


def test_update_user_status_manager_forbidden(
    client: TestClient,
    create_user,
    get_token,
):
    manager = create_user(
        email="manager@example.com",
        role="manager",
    )

    target = create_user(
        email="target@example.com",
        role="member",
    )

    token = get_token(manager.email)

    response = client.patch(
        f"/users/{target.id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_active": False},
    )

    assert response.status_code == 403


@pytest.mark.parametrize(
    "value",
    [
        True,
        False,
        "true",
        "false",
        1,
        0,
        "yes",
        "no",
    ],
)
def test_update_user_status_accepts_boolean_values(
    client: TestClient,
    create_user,
    get_token,
    value,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
    )

    user = create_user(
        email="user@example.com",
        role="member",
    )

    token = get_token(admin.email)

    response = client.patch(
        f"/users/{user.id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_active": value},
    )

    assert response.status_code == 200


def test_update_user_status_rejects_null(
    client: TestClient,
    create_user,
    get_token,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
    )

    user = create_user(
        email="user@example.com",
        role="member",
    )

    token = get_token(admin.email)

    response = client.patch(
        f"/users/{user.id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_active": None},
    )

    assert response.status_code == 422

def test_update_user_status_missing_field(
    client: TestClient,
    create_user,
    get_token,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
    )

    user = create_user(
        email="user@example.com",
        role="member",
    )

    token = get_token(admin.email)

    response = client.patch(
        f"/users/{user.id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )

    assert response.status_code == 422


# ============================================================
# Response security
# ============================================================


def test_user_response_does_not_expose_password_hash(
    client: TestClient,
    create_user,
    get_token,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
    )

    target = create_user(
        email="target@example.com",
        role="member",
    )

    token = get_token(admin.email)

    response = client.get(
        f"/users/{target.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert "password_hash" not in data
    assert "password" not in data


def test_list_users_does_not_expose_password_hash(
    client: TestClient,
    create_user,
    get_token,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
    )

    create_user(
        email="target@example.com",
        role="member",
    )

    token = get_token(admin.email)

    response = client.get(
        "/users",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    for user in response.json():
        assert "password_hash" not in user
        assert "password" not in user