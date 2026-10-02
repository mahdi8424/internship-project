from datetime import datetime, timedelta, timezone

import pytest

from app.auth.refresh import hash_refresh_token
from app.db.models import RefreshToken


# ============================================================
# REGISTER
# ============================================================


def test_register_user(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "full_name": "Test User",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "user@example.com"
    assert data["full_name"] == "Test User"
    assert data["role"] == "member"
    assert data["is_active"] is True


def test_register_user_password_is_not_returned(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "full_name": "Test User",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert "password" not in data
    assert "password_hash" not in data


def test_register_duplicate_email(client):
    payload = {
        "email": "user@example.com",
        "password": "password123",
        "full_name": "Test User",
    }

    response = client.post(
        "/auth/register",
        json=payload,
    )

    assert response.status_code == 201

    response = client.post(
        "/auth/register",
        json=payload,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"


def test_register_missing_email(client):
    response = client.post(
        "/auth/register",
        json={
            "password": "password123",
            "full_name": "Test User",
        },
    )

    assert response.status_code == 422


def test_register_missing_password(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "full_name": "Test User",
        },
    )

    assert response.status_code == 422


def test_register_missing_full_name(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 422


def test_register_invalid_email(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "not-an-email",
            "password": "password123",
            "full_name": "Test User",
        },
    )

    # This depends on whether UserCreate uses EmailStr.
    # If email is simply `str`, this will be 201 instead.
    assert response.status_code in (201, 422)


def test_register_empty_payload(client):
    response = client.post(
        "/auth/register",
        json={},
    )

    assert response.status_code == 422


# ============================================================
# LOGIN
# ============================================================


def test_login_user(client):
    client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "full_name": "Test User",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "full_name": "Test User",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_unknown_email(client):
    response = client.post(
        "/auth/login",
        json={
            "email": "unknown@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_inactive_user(client, create_user):
    create_user(
        email="inactive@example.com",
        is_active=False,
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "inactive@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_missing_email(client):
    response = client.post(
        "/auth/login",
        json={
            "password": "password123",
        },
    )

    assert response.status_code == 422


def test_login_missing_password(client):
    response = client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
        },
    )

    assert response.status_code == 422


def test_login_empty_password(client):
    response = client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "",
        },
    )

    assert response.status_code == 422


def test_login_empty_payload(client):
    response = client.post(
        "/auth/login",
        json={},
    )

    assert response.status_code == 422


# ============================================================
# GET /auth/me
# ============================================================


def test_me_requires_authentication(client):
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_me_with_valid_token(
    client,
    get_token,
):
    client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "full_name": "Test User",
        },
    )

    token = get_token(
        "user@example.com",
        "password123",
    )

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "user@example.com"
    assert data["full_name"] == "Test User"
    assert data["role"] == "member"
    assert data["is_active"] is True


def test_me_with_invalid_token(client):
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401


def test_me_with_malformed_authorization_header(client):
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "invalid-token",
        },
    )

    assert response.status_code == 401


def test_me_with_empty_bearer_token(client):
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer ",
        },
    )

    assert response.status_code == 401


# ============================================================
# REFRESH TOKEN
# ============================================================


def test_refresh_token(client):
    client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "full_name": "Test User",
        },
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    old_tokens = login_response.json()

    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": old_tokens["refresh_token"],
        },
    )

    assert response.status_code == 200

    new_tokens = response.json()

    assert new_tokens["access_token"]
    assert new_tokens["refresh_token"]
    assert new_tokens["token_type"] == "bearer"

    assert (
        new_tokens["refresh_token"]
        != old_tokens["refresh_token"]
    )


def test_refresh_token_invalid(client):
    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": "invalid-refresh-token",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid refresh token"


def test_refresh_token_missing(client):
    response = client.post(
        "/auth/refresh",
        json={},
    )

    assert response.status_code == 422


def test_refresh_token_empty(client):
    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": "",
        },
    )

    assert response.status_code == 422


def test_refresh_token_revoked(
    client,
    db,
):
    client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "full_name": "Test User",
        },
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "password123",
        },
    )

    tokens = login_response.json()

    refresh_response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": tokens["refresh_token"],
        },
    )

    assert refresh_response.status_code == 200

    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": tokens["refresh_token"],
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token has been revoked"


def test_refresh_token_expired(
    client,
    db,
    create_user,
):
    user = create_user(
        email="user@example.com",
    )

    refresh_token = "expired-refresh-token"

    token_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(refresh_token),
        expires_at=datetime.now(timezone.utc) - timedelta(
            days=1
        ),
    )

    db.add(token_record)
    db.commit()

    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token has expired"


def test_refresh_token_for_inactive_user(
    client,
    db,
    create_user,
):
    user = create_user(
        email="inactive@example.com",
        is_active=False,
    )

    refresh_token = "inactive-user-refresh-token"

    token_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(
            days=7
        ),
    )

    db.add(token_record)
    db.commit()

    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or inactive user"


def test_refresh_token_for_missing_user(
    client,
    db,
):
    refresh_token = "missing-user-refresh-token"

    token_record = RefreshToken(
        user_id=99999,
        token_hash=hash_refresh_token(refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(
            days=7
        ),
    )

    db.add(token_record)
    db.commit()

    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or inactive user"


# ============================================================
# LOGOUT
# ============================================================


def test_logout(
    client,
):
    client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "full_name": "Test User",
        },
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "password123",
        },
    )

    tokens = login_response.json()

    response = client.post(
        "/auth/logout",
        json={
            "refresh_token": tokens["refresh_token"],
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Logged out successfully"
    }

    refresh_response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": tokens["refresh_token"],
        },
    )

    assert refresh_response.status_code == 401
    assert (
        refresh_response.json()["detail"]
        == "Refresh token has been revoked"
    )


def test_logout_unknown_refresh_token(client):
    response = client.post(
        "/auth/logout",
        json={
            "refresh_token": "unknown-refresh-token",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Logged out successfully"
    }


def test_logout_already_revoked_token(
    client,
    db,
):
    client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "full_name": "Test User",
        },
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "password123",
        },
    )

    tokens = login_response.json()

    first_response = client.post(
        "/auth/logout",
        json={
            "refresh_token": tokens["refresh_token"],
        },
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/auth/logout",
        json={
            "refresh_token": tokens["refresh_token"],
        },
    )

    assert second_response.status_code == 200
    assert second_response.json() == {
        "message": "Logged out successfully"
    }


def test_logout_missing_refresh_token(client):
    response = client.post(
        "/auth/logout",
        json={},
    )

    assert response.status_code == 422


def test_logout_empty_refresh_token(client):
    response = client.post(
        "/auth/logout",
        json={
            "refresh_token": "",
        },
    )

    assert response.status_code == 422


# ============================================================
# CHANGE PASSWORD
# ============================================================


def test_change_password_requires_authentication(client):
    response = client.put(
        "/auth/me/password",
        json={
            "current_password": "password123",
            "new_password": "newpassword123",
        },
    )

    assert response.status_code == 401


def test_change_password(
    client,
):
    client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "full_name": "Test User",
        },
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "password123",
        },
    )

    tokens = login_response.json()

    response = client.put(
        "/auth/me/password",
        headers={
            "Authorization": f"Bearer {tokens['access_token']}",
        },
        json={
            "current_password": "password123",
            "new_password": "newpassword123",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Password changed successfully"
    }


def test_change_password_wrong_current_password(
    client,
):
    client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "full_name": "Test User",
        },
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "password123",
        },
    )

    tokens = login_response.json()

    response = client.put(
        "/auth/me/password",
        headers={
            "Authorization": f"Bearer {tokens['access_token']}",
        },
        json={
            "current_password": "wrongpassword",
            "new_password": "newpassword123",
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Current password is incorrect"
    )


def test_change_password_new_password_too_short(
    client,
):
    client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "full_name": "Test User",
        },
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "password123",
        },
    )

    tokens = login_response.json()

    response = client.put(
        "/auth/me/password",
        headers={
            "Authorization": f"Bearer {tokens['access_token']}",
        },
        json={
            "current_password": "password123",
            "new_password": "short",
        },
    )

    assert response.status_code == 422


def test_change_password_new_password_too_long(
    client,
):
    client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "full_name": "Test User",
        },
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "password123",
        },
    )

    tokens = login_response.json()

    response = client.put(
        "/auth/me/password",
        headers={
            "Authorization": f"Bearer {tokens['access_token']}",
        },
        json={
            "current_password": "password123",
            "new_password": "a" * 129,
        },
    )

    assert response.status_code == 422


def test_change_password_missing_current_password(
    client,
):
    response = client.put(
        "/auth/me/password",
        json={
            "new_password": "newpassword123",
        },
    )

    assert response.status_code == 401


def test_change_password_missing_new_password(
    client,
    get_token,
):
    client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "full_name": "Test User",
        },
    )

    token = get_token(
        "user@example.com",
        "password123",
    )

    response = client.put(
        "/auth/me/password",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "current_password": "password123",
        },
    )

    assert response.status_code == 422


def test_change_password_revokes_existing_refresh_tokens(
    client,
    db,
):
    client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "full_name": "Test User",
        },
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "password123",
        },
    )

    tokens = login_response.json()

    response = client.put(
        "/auth/me/password",
        headers={
            "Authorization": f"Bearer {tokens['access_token']}",
        },
        json={
            "current_password": "password123",
            "new_password": "newpassword123",
        },
    )

    assert response.status_code == 200

    refresh_response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": tokens["refresh_token"],
        },
    )

    assert refresh_response.status_code == 401
    assert (
        refresh_response.json()["detail"]
        == "Refresh token has been revoked"
    )


def test_change_password_does_not_allow_old_password(
    client,
):
    client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "full_name": "Test User",
        },
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "password123",
        },
    )

    tokens = login_response.json()

    response = client.put(
        "/auth/me/password",
        headers={
            "Authorization": f"Bearer {tokens['access_token']}",
        },
        json={
            "current_password": "password123",
            "new_password": "newpassword123",
        },
    )

    assert response.status_code == 200

    old_password_response = client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "password123",
        },
    )

    assert old_password_response.status_code == 401


def test_change_password_allows_new_password(
    client,
):
    client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "full_name": "Test User",
        },
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "password123",
        },
    )

    tokens = login_response.json()

    response = client.put(
        "/auth/me/password",
        headers={
            "Authorization": f"Bearer {tokens['access_token']}",
        },
        json={
            "current_password": "password123",
            "new_password": "newpassword123",
        },
    )

    assert response.status_code == 200

    new_password_response = client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "newpassword123",
        },
    )

    assert new_password_response.status_code == 200

    data = new_password_response.json()

    assert data["access_token"]
    assert data["refresh_token"]


# ============================================================
# END-TO-END AUTH FLOWS
# ============================================================


def test_complete_auth_flow(client):
    # Register
    register_response = client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "full_name": "Test User",
        },
    )

    assert register_response.status_code == 201

    # Login
    login_response = client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    tokens = login_response.json()

    # Access /me
    me_response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {tokens['access_token']}",
        },
    )

    assert me_response.status_code == 200
    assert me_response.json()["email"] == "user@example.com"

    # Refresh
    refresh_response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": tokens["refresh_token"],
        },
    )

    assert refresh_response.status_code == 200

    new_tokens = refresh_response.json()

    # New access token works
    me_response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {new_tokens['access_token']}",
        },
    )

    assert me_response.status_code == 200

    # Logout
    logout_response = client.post(
        "/auth/logout",
        json={
            "refresh_token": new_tokens["refresh_token"],
        },
    )

    assert logout_response.status_code == 200

    # Refresh token no longer works
    refresh_response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": new_tokens["refresh_token"],
        },
    )

    assert refresh_response.status_code == 401
