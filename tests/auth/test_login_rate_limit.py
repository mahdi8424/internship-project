from datetime import datetime, timedelta, timezone

from app.auth.password import hash_password
from app.db.models import LoginAttempt, User


def create_test_user(db):
    user = User(
        email="ratelimit@example.com",
        password_hash=hash_password("correct-password"),
        full_name="Rate Limit User",
        role="member",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def login_payload(
    email="ratelimit@example.com",
    password="wrong-password",
):
    return {
        "email": email,
        "password": password,
    }


def test_login_rate_limit_after_five_failed_attempts(
    client,
    db,
):
    create_test_user(db)

    for _ in range(5):
        response = client.post(
            "/auth/login",
            json=login_payload(),
        )

        assert response.status_code == 401

    response = client.post(
        "/auth/login",
        json=login_payload(),
    )

    assert response.status_code == 429
    assert response.json()["detail"] == (
        "Too many failed login attempts. Please try again later."
    )


def test_successful_login_clears_failed_attempts(
    client,
    db,
):
    create_test_user(db)

    for _ in range(4):
        response = client.post(
            "/auth/login",
            json=login_payload(),
        )

        assert response.status_code == 401

    response = client.post(
        "/auth/login",
        json=login_payload(
            password="correct-password",
        ),
    )

    assert response.status_code == 200

    attempts = db.query(LoginAttempt).all()

    assert attempts == []


def test_rate_limit_is_scoped_to_email_and_ip(
    client,
    db,
):
    create_test_user(db)

    for _ in range(5):
        response = client.post(
            "/auth/login",
            json=login_payload(),
        )

        assert response.status_code == 401

    blocked = client.post(
        "/auth/login",
        json=login_payload(),
    )

    assert blocked.status_code == 429

    other_user = User(
        email="other@example.com",
        password_hash=hash_password("correct-password"),
        full_name="Other User",
        role="member",
        is_active=True,
    )

    db.add(other_user)
    db.commit()

    response = client.post(
        "/auth/login",
        json={
            "email": "other@example.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401


def test_old_failed_attempts_do_not_count(
    client,
    db,
):
    create_test_user(db)

    old_time = datetime.now(timezone.utc) - timedelta(
        seconds=61,
    )

    for _ in range(5):
        db.add(
            LoginAttempt(
                email="ratelimit@example.com",
                ip_address="testclient",
                attempted_at=old_time,
            )
        )

    db.commit()

    response = client.post(
        "/auth/login",
        json=login_payload(),
    )

    assert response.status_code == 401

def test_rate_limit_blocks_correct_password_after_limit(
    client,
    db,
):
    create_test_user(db)

    for _ in range(5):
        response = client.post(
            "/auth/login",
            json=login_payload(),
        )

        assert response.status_code == 401

    response = client.post(
        "/auth/login",
        json=login_payload(
            password="correct-password",
        ),
    )

    assert response.status_code == 429

def test_old_attempts_are_ignored(
    client,
    db,
):
    create_test_user(db)

    old_time = datetime.now(timezone.utc) - timedelta(
        seconds=61,
    )

    for _ in range(5):
        db.add(
            LoginAttempt(
                email="ratelimit@example.com",
                ip_address="testclient",
                attempted_at=old_time,
            )
        )

    db.commit()

    response = client.post(
        "/auth/login",
        json=login_payload(),
    )

    assert response.status_code == 401