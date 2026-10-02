# tests/users/test_users.py

from app.db.models import User


# ============================================================
# HELPERS
# ============================================================


def auth_header(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
    }


def create_admin(create_user):
    return create_user(
        email="admin@example.com",
        role="admin",
        full_name="Admin User",
    )


def create_manager(create_user, email="manager@example.com"):
    return create_user(
        email=email,
        role="manager",
        full_name="Manager User",
    )


def create_member(create_user, email="member@example.com"):
    return create_user(
        email=email,
        role="member",
        full_name="Member User",
    )


# ============================================================
# GET /users
# ============================================================


def test_list_users_requires_authentication(client):
    response = client.get("/users")

    assert response.status_code == 401


def test_list_users_admin_allowed(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)

    create_user(
        email="user1@example.com",
        full_name="User One",
    )
    create_user(
        email="user2@example.com",
        full_name="User Two",
    )

    token = get_token(
        admin.email,
        "password123",
    )

    response = client.get(
        "/users",
        headers=auth_header(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 3

    assert data[0]["id"] < data[1]["id"]
    assert data[1]["id"] < data[2]["id"]


def test_list_users_manager_forbidden(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)

    token = get_token(
        manager.email,
        "password123",
    )

    response = client.get(
        "/users",
        headers=auth_header(token),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"


def test_list_users_member_forbidden(
    client,
    create_user,
    get_token,
):
    member = create_member(create_user)

    token = get_token(
        member.email,
        "password123",
    )

    response = client.get(
        "/users",
        headers=auth_header(token),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"


def test_list_users_pagination_first_page(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)

    for index in range(1, 6):
        create_user(
            email=f"user{index}@example.com",
            full_name=f"User {index}",
        )

    token = get_token(
        admin.email,
        "password123",
    )

    response = client.get(
        "/users?page=1&page_size=2",
        headers=auth_header(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["email"] == "admin@example.com"
    assert data[1]["email"] == "user1@example.com"


def test_list_users_pagination_second_page(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)

    for index in range(1, 6):
        create_user(
            email=f"user{index}@example.com",
            full_name=f"User {index}",
        )

    token = get_token(
        admin.email,
        "password123",
    )

    response = client.get(
        "/users?page=2&page_size=2",
        headers=auth_header(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["email"] == "user2@example.com"
    assert data[1]["email"] == "user3@example.com"


def test_list_users_pagination_last_partial_page(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)

    for index in range(1, 5):
        create_user(
            email=f"user{index}@example.com",
            full_name=f"User {index}",
        )

    token = get_token(
        admin.email,
        "password123",
    )

    response = client.get(
        "/users?page=3&page_size=2",
        headers=auth_header(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["email"] == "user4@example.com"


def test_list_users_page_beyond_available_data(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)

    create_user(
        email="user@example.com",
    )

    token = get_token(
        admin.email,
        "password123",
    )

    response = client.get(
        "/users?page=10&page_size=20",
        headers=auth_header(token),
    )

    assert response.status_code == 200
    assert response.json() == []


def test_list_users_invalid_page_zero(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)

    token = get_token(
        admin.email,
        "password123",
    )

    response = client.get(
        "/users?page=0",
        headers=auth_header(token),
    )

    assert response.status_code == 422


def test_list_users_invalid_page_negative(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)

    token = get_token(
        admin.email,
        "password123",
    )

    response = client.get(
        "/users?page=-1",
        headers=auth_header(token),
    )

    assert response.status_code == 422


def test_list_users_invalid_page_size_zero(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)

    token = get_token(
        admin.email,
        "password123",
    )

    response = client.get(
        "/users?page_size=0",
        headers=auth_header(token),
    )

    assert response.status_code == 422


def test_list_users_page_size_over_100(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)

    token = get_token(
        admin.email,
        "password123",
    )

    response = client.get(
        "/users?page_size=101",
        headers=auth_header(token),
    )

    assert response.status_code == 422


# ============================================================
# GET /users/{user_id}
# ============================================================


def test_get_user_requires_authentication(
    client,
    create_user,
):
    user = create_user(
        email="user@example.com",
    )

    response = client.get(
        f"/users/{user.id}",
    )

    assert response.status_code == 401


def test_get_user_admin_allowed(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)

    user = create_user(
        email="target@example.com",
        full_name="Target User",
        role="member",
    )

    token = get_token(
        admin.email,
        "password123",
    )

    response = client.get(
        f"/users/{user.id}",
        headers=auth_header(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == user.id
    assert data["email"] == "target@example.com"
    assert data["full_name"] == "Target User"
    assert data["role"] == "member"
    assert data["is_active"] is True


def test_get_user_manager_forbidden(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)

    user = create_user(
        email="target@example.com",
    )

    token = get_token(
        manager.email,
        "password123",
    )

    response = client.get(
        f"/users/{user.id}",
        headers=auth_header(token),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"


def test_get_user_member_forbidden(
    client,
    create_user,
    get_token,
):
    member = create_member(create_user)

    user = create_user(
        email="target@example.com",
    )

    token = get_token(
        member.email,
        "password123",
    )

    response = client.get(
        f"/users/{user.id}",
        headers=auth_header(token),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"


def test_get_user_not_found(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)

    token = get_token(
        admin.email,
        "password123",
    )

    response = client.get(
        "/users/99999",
        headers=auth_header(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


# ============================================================
# PATCH /users/{user_id}/role
# ============================================================


def test_update_user_role_requires_authentication(
    client,
    create_user,
):
    user = create_user(
        email="target@example.com",
    )

    response = client.patch(
        f"/users/{user.id}/role",
        json={
            "role": "manager",
        },
    )

    assert response.status_code == 401


def test_update_user_role_admin_allowed(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)

    user = create_user(
        email="target@example.com",
        role="member",
    )

    token = get_token(
        admin.email,
        "password123",
    )

    response = client.patch(
        f"/users/{user.id}/role",
        headers=auth_header(token),
        json={
            "role": "manager",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == user.id
    assert data["role"] == "manager"


def test_update_user_role_manager_forbidden(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)

    user = create_user(
        email="target@example.com",
        role="member",
    )

    token = get_token(
        manager.email,
        "password123",
    )

    response = client.patch(
        f"/users/{user.id}/role",
        headers=auth_header(token),
        json={
            "role": "manager",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"


def test_update_user_role_member_forbidden(
    client,
    create_user,
    get_token,
):
    member = create_member(create_user)

    user = create_user(
        email="target@example.com",
        role="member",
    )

    token = get_token(
        member.email,
        "password123",
    )

    response = client.patch(
        f"/users/{user.id}/role",
        headers=auth_header(token),
        json={
            "role": "manager",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"


def test_update_user_role_not_found(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)

    token = get_token(
        admin.email,
        "password123",
    )

    response = client.patch(
        "/users/99999/role",
        headers=auth_header(token),
        json={
            "role": "manager",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_update_user_role_invalid_role(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)

    user = create_user(
        email="target@example.com",
    )

    token = get_token(
        admin.email,
        "password123",
    )

    response = client.patch(
        f"/users/{user.id}/role",
        headers=auth_header(token),
        json={
            "role": "superuser",
        },
    )

    assert response.status_code == 422


def test_update_user_role_missing_role(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)

    user = create_user(
        email="target@example.com",
    )

    token = get_token(
        admin.email,
        "password123",
    )

    response = client.patch(
        f"/users/{user.id}/role",
        headers=auth_header(token),
        json={},
    )

    assert response.status_code == 422


def test_admin_cannot_remove_own_admin_role(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)

    token = get_token(
        admin.email,
        "password123",
    )

    response = client.patch(
        f"/users/{admin.id}/role",
        headers=auth_header(token),
        json={
            "role": "manager",
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "You cannot remove your own admin role"
    )


def test_admin_can_keep_own_admin_role(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)

    token = get_token(
        admin.email,
        "password123",
    )

    response = client.patch(
        f"/users/{admin.id}/role",
        headers=auth_header(token),
        json={
            "role": "admin",
        },
    )

    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_admin_can_change_member_to_manager(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)

    user = create_user(
        email="member@example.com",
        role="member",
    )

    token = get_token(
        admin.email,
        "password123",
    )

    response = client.patch(
        f"/users/{user.id}/role",
        headers=auth_header(token),
        json={
            "role": "manager",
        },
    )

    assert response.status_code == 200
    assert response.json()["role"] == "manager"


def test_admin_can_change_manager_to_member(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)

    user = create_user(
        email="manager@example.com",
        role="manager",
    )

    token = get_token(
        admin.email,
        "password123",
    )

    response = client.patch(
        f"/users/{user.id}/role",
        headers=auth_header(token),
        json={
            "role": "member",
        },
    )

    assert response.status_code == 200
    assert response.json()["role"] == "member"


# ============================================================
# PATCH /users/{user_id}/status
# ============================================================


def test_update_user_status_requires_authentication(
    client,
    create_user,
):
    user = create_user(
        email="target@example.com",
    )

    response = client.patch(
        f"/users/{user.id}/status",
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 401


def test_update_user_status_admin_allowed(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)

    user = create_user(
        email="target@example.com",
        is_active=True,
    )

    token = get_token(
        admin.email,
        "password123",
    )

    response = client.patch(
        f"/users/{user.id}/status",
        headers=auth_header(token),
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == user.id
    assert data["is_active"] is False


def test_update_user_status_manager_forbidden(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)

    user = create_user(
        email="target@example.com",
        is_active=True,
    )

    token = get_token(
        manager.email,
        "password123",
    )

    response = client.patch(
        f"/users/{user.id}/status",
        headers=auth_header(token),
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"


def test_update_user_status_member_forbidden(
    client,
    create_user,
    get_token,
):
    member = create_member(create_user)

    user = create_user(
        email="target@example.com",
        is_active=True,
    )

    token = get_token(
        member.email,
        "password123",
    )

    response = client.patch(
        f"/users/{user.id}/status",
        headers=auth_header(token),
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"


def test_update_user_status_not_found(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)

    token = get_token(
        admin.email,
        "password123",
    )

    response = client.patch(
        "/users/99999/status",
        headers=auth_header(token),
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_admin_can_activate_user(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)

    user = create_user(
        email="inactive@example.com",
        is_active=False,
    )

    token = get_token(
        admin.email,
        "password123",
    )

    response = client.patch(
        f"/users/{user.id}/status",
        headers=auth_header(token),
        json={
            "is_active": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is True


def test_admin_can_deactivate_user(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)

    user = create_user(
        email="active@example.com",
        is_active=True,
    )

    token = get_token(
        admin.email,
        "password123",
    )

    response = client.patch(
        f"/users/{user.id}/status",
        headers=auth_header(token),
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_admin_cannot_deactivate_own_account(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)

    token = get_token(
        admin.email,
        "password123",
    )

    response = client.patch(
        f"/users/{admin.id}/status",
        headers=auth_header(token),
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "You cannot deactivate your own account"
    )


def test_admin_can_keep_own_account_active(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)

    token = get_token(
        admin.email,
        "password123",
    )

    response = client.patch(
        f"/users/{admin.id}/status",
        headers=auth_header(token),
        json={
            "is_active": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is True


def test_update_user_status_missing_is_active(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)

    user = create_user(
        email="target@example.com",
    )

    token = get_token(
        admin.email,
        "password123",
    )

    response = client.patch(
        f"/users/{user.id}/status",
        headers=auth_header(token),
        json={},
    )

    assert response.status_code == 422


def test_update_user_status_invalid_type(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)

    user = create_user(
        email="target@example.com",
    )

    token = get_token(
        admin.email,
        "password123",
    )

    response = client.patch(
        f"/users/{user.id}/status",
        headers=auth_header(token),
        json={
            "is_active": [],
        },
    )

    assert response.status_code == 422


# ============================================================
# RESPONSE / DATABASE CONSISTENCY
# ============================================================


def test_update_user_role_persists(
    client,
    create_user,
    get_token,
    db,
):
    admin = create_admin(create_user)

    user = create_user(
        email="target@example.com",
        role="member",
    )

    token = get_token(
        admin.email,
        "password123",
    )

    response = client.patch(
        f"/users/{user.id}/role",
        headers=auth_header(token),
        json={
            "role": "manager",
        },
    )

    assert response.status_code == 200

    db.expire_all()

    updated_user = db.get(User, user.id)

    assert updated_user is not None
    assert updated_user.role == "manager"


def test_update_user_status_persists(
    client,
    create_user,
    get_token,
    db,
):
    admin = create_admin(create_user)

    user = create_user(
        email="target@example.com",
        is_active=True,
    )

    token = get_token(
        admin.email,
        "password123",
    )

    response = client.patch(
        f"/users/{user.id}/status",
        headers=auth_header(token),
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 200

    db.expire_all()

    updated_user = db.get(User, user.id)

    assert updated_user is not None
    assert updated_user.is_active is False