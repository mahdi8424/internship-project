import pytest
from fastapi.testclient import TestClient


# ============================================================
# POST /projects
# ============================================================


def test_create_project(
    client: TestClient,
    create_user,
    get_token,
):
    user = create_user(
        email="owner@example.com",
        role="member",
    )

    token = get_token(user.email)

    response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Test Project",
            "description": "A test project",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Test Project"
    assert data["description"] == "A test project"
    assert data["owner_id"] == user.id
    assert "id" in data
    assert "created_at" in data


def test_create_project_without_description(
    client: TestClient,
    create_user,
    get_token,
):
    user = create_user(
        email="owner@example.com",
    )

    token = get_token(user.email)

    response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Test Project",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Test Project"
    assert data["description"] is None
    assert data["owner_id"] == user.id


def test_create_project_requires_authentication(
    client: TestClient,
):
    response = client.post(
        "/projects",
        json={
            "name": "Test Project",
        },
    )

    assert response.status_code == 401


def test_create_project_invalid_token(
    client: TestClient,
):
    response = client.post(
        "/projects",
        headers={"Authorization": "Bearer invalid-token"},
        json={
            "name": "Test Project",
        },
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"description": "Missing name"},
        {"name": ""},
        {"name": None},
    ],
)
def test_create_project_invalid_name(
    client: TestClient,
    create_user,
    get_token,
    payload,
):
    user = create_user(
        email="owner@example.com",
    )

    token = get_token(user.email)

    response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )

    assert response.status_code == 422


def test_create_project_name_too_long(
    client: TestClient,
    create_user,
    get_token,
):
    user = create_user(
        email="owner@example.com",
    )

    token = get_token(user.email)

    response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "a" * 256,
        },
    )

    assert response.status_code == 422


def test_create_project_name_max_length(
    client: TestClient,
    create_user,
    get_token,
):
    user = create_user(
        email="owner@example.com",
    )

    token = get_token(user.email)

    response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "a" * 255,
        },
    )

    assert response.status_code == 201


# ============================================================
# GET /projects
# ============================================================


def test_list_projects_as_admin(
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

    admin_token = get_token(admin.email)
    user_token = get_token(user.email)

    create_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Admin Project"},
    )
    assert create_response.status_code == 201

    create_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"name": "User Project"},
    )
    assert create_response.status_code == 201

    response = client.get(
        "/projects",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["name"] == "Admin Project"
    assert data[1]["name"] == "User Project"


def test_list_projects_as_regular_user_only_returns_owned_or_member_projects(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
        role="member",
    )

    other_user = create_user(
        email="other@example.com",
        role="member",
    )

    owner_token = get_token(owner.email)
    other_token = get_token(other_user.email)

    owned_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Owned Project"},
    )
    assert owned_response.status_code == 201

    other_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {other_token}"},
        json={"name": "Other Project"},
    )
    assert other_response.status_code == 201

    response = client.get(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Owned Project"


def test_list_projects_includes_project_where_user_is_member(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
        role="member",
    )

    member = create_user(
        email="member@example.com",
        role="member",
    )

    owner_token = get_token(owner.email)
    member_token = get_token(member.email)

    create_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Shared Project"},
    )

    assert create_response.status_code == 201

    project_id = create_response.json()["id"]

    add_response = client.post(
        f"/projects/{project_id}/members/{member.id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert add_response.status_code == 201

    response = client.get(
        "/projects",
        headers={"Authorization": f"Bearer {member_token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == project_id
    assert data[0]["name"] == "Shared Project"


def test_list_projects_requires_authentication(
    client: TestClient,
):
    response = client.get("/projects")

    assert response.status_code == 401


def test_list_projects_pagination(
    client: TestClient,
    create_user,
    get_token,
):
    user = create_user(
        email="user@example.com",
    )

    token = get_token(user.email)

    for index in range(5):
        response = client.post(
            "/projects",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": f"Project {index + 1}"},
        )
        assert response.status_code == 201

    response = client.get(
        "/projects?page=1&page_size=2",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["name"] == "Project 1"
    assert data[1]["name"] == "Project 2"


def test_list_projects_second_page(
    client: TestClient,
    create_user,
    get_token,
):
    user = create_user(
        email="user@example.com",
    )

    token = get_token(user.email)

    for index in range(5):
        response = client.post(
            "/projects",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": f"Project {index + 1}"},
        )
        assert response.status_code == 201

    response = client.get(
        "/projects?page=2&page_size=2",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["name"] == "Project 3"
    assert data[1]["name"] == "Project 4"


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
def test_list_projects_invalid_pagination(
    client: TestClient,
    create_user,
    get_token,
    query,
):
    user = create_user(
        email="user@example.com",
    )

    token = get_token(user.email)

    response = client.get(
        f"/projects{query}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


# ============================================================
# GET /projects/{project_id}
# ============================================================


def test_get_project_as_owner(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    token = get_token(owner.email)

    create_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Test Project",
            "description": "Description",
        },
    )

    assert create_response.status_code == 201

    project_id = create_response.json()["id"]

    response = client.get(
        f"/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == project_id
    assert data["name"] == "Test Project"
    assert data["description"] == "Description"
    assert data["owner_id"] == owner.id


def test_get_project_as_member(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    member = create_user(
        email="member@example.com",
    )

    owner_token = get_token(owner.email)
    member_token = get_token(member.email)

    create_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Shared Project"},
    )

    assert create_response.status_code == 201

    project_id = create_response.json()["id"]

    add_response = client.post(
        f"/projects/{project_id}/members/{member.id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert add_response.status_code == 201

    response = client.get(
        f"/projects/{project_id}",
        headers={"Authorization": f"Bearer {member_token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == project_id
    assert data["name"] == "Shared Project"


def test_get_project_non_member_forbidden(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    other_user = create_user(
        email="other@example.com",
    )

    owner_token = get_token(owner.email)
    other_token = get_token(other_user.email)

    create_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Private Project"},
    )

    assert create_response.status_code == 201

    project_id = create_response.json()["id"]

    response = client.get(
        f"/projects/{project_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 403


def test_get_project_not_found(
    client: TestClient,
    create_user,
    get_token,
):
    user = create_user(
        email="user@example.com",
    )

    token = get_token(user.email)

    response = client.get(
        "/projects/999999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_get_project_requires_authentication(
    client: TestClient,
):
    response = client.get("/projects/1")

    assert response.status_code == 401


@pytest.mark.parametrize(
    "project_id",
    [
        "abc",
        "1.5",
        "invalid",
    ],
)
def test_get_project_invalid_id(
    client: TestClient,
    create_user,
    get_token,
    project_id,
):
    user = create_user(
        email="user@example.com",
    )

    token = get_token(user.email)

    response = client.get(
        f"/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


# ============================================================
# PATCH /projects/{project_id}
# ============================================================


def test_update_project_name(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    token = get_token(owner.email)

    create_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Original Name",
            "description": "Original Description",
        },
    )

    assert create_response.status_code == 201

    project_id = create_response.json()["id"]

    response = client.patch(
        f"/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Updated Name"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Updated Name"
    assert data["description"] == "Original Description"


def test_update_project_description(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    token = get_token(owner.email)

    create_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Test Project",
            "description": "Original Description",
        },
    )

    assert create_response.status_code == 201

    project_id = create_response.json()["id"]

    response = client.patch(
        f"/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"description": "Updated Description"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Test Project"
    assert data["description"] == "Updated Description"


def test_update_project_name_and_description(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    token = get_token(owner.email)

    create_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Original Name",
            "description": "Original Description",
        },
    )

    assert create_response.status_code == 201

    project_id = create_response.json()["id"]

    response = client.patch(
        f"/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Updated Name",
            "description": "Updated Description",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Updated Name"
    assert data["description"] == "Updated Description"


def test_update_project_with_empty_payload(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    token = get_token(owner.email)

    create_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Original Name",
            "description": "Original Description",
        },
    )

    assert create_response.status_code == 201

    project_id = create_response.json()["id"]

    response = client.patch(
        f"/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Original Name"
    assert data["description"] == "Original Description"


def test_update_project_description_null_does_not_clear_description(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    token = get_token(owner.email)

    create_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Test Project",
            "description": "Original Description",
        },
    )

    assert create_response.status_code == 201

    project_id = create_response.json()["id"]

    response = client.patch(
        f"/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"description": None},
    )

    assert response.status_code == 200

    data = response.json()

    # The route only updates description when it is not None.
    assert data["description"] == "Original Description"


def test_update_project_non_owner_forbidden(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    other_user = create_user(
        email="other@example.com",
    )

    owner_token = get_token(owner.email)
    other_token = get_token(other_user.email)

    create_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Owner Project"},
    )

    assert create_response.status_code == 201

    project_id = create_response.json()["id"]

    response = client.patch(
        f"/projects/{project_id}",
        headers={"Authorization": f"Bearer {other_token}"},
        json={"name": "Updated"},
    )

    assert response.status_code == 403


def test_update_project_not_found(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    token = get_token(owner.email)

    response = client.patch(
        "/projects/999999",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Updated"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_update_project_requires_authentication(
    client: TestClient,
):
    response = client.patch(
        "/projects/1",
        json={"name": "Updated"},
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    "payload",
    [
        {"name": ""},
        {"name": "a" * 256},
    ],
)
def test_update_project_invalid_name(
    client: TestClient,
    create_user,
    get_token,
    payload,
):
    owner = create_user(
        email="owner@example.com",
    )

    token = get_token(owner.email)

    create_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Original"},
    )

    assert create_response.status_code == 201

    project_id = create_response.json()["id"]

    response = client.patch(
        f"/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )

    assert response.status_code == 422


def test_update_project_name_max_length(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    token = get_token(owner.email)

    create_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Original"},
    )

    assert create_response.status_code == 201

    project_id = create_response.json()["id"]

    response = client.patch(
        f"/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "a" * 255},
    )

    assert response.status_code == 200


# ============================================================
# DELETE /projects/{project_id}
# ============================================================


def test_delete_project(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    token = get_token(owner.email)

    create_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Project To Delete"},
    )

    assert create_response.status_code == 201

    project_id = create_response.json()["id"]

    response = client.delete(
        f"/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204
    assert response.content == b""

    get_response = client.get(
        f"/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert get_response.status_code == 404


def test_delete_project_non_owner_forbidden(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    other_user = create_user(
        email="other@example.com",
    )

    owner_token = get_token(owner.email)
    other_token = get_token(other_user.email)

    create_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Owner Project"},
    )

    assert create_response.status_code == 201

    project_id = create_response.json()["id"]

    response = client.delete(
        f"/projects/{project_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 403


def test_delete_project_not_found(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    token = get_token(owner.email)

    response = client.delete(
        "/projects/999999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_delete_project_requires_authentication(
    client: TestClient,
):
    response = client.delete("/projects/1")

    assert response.status_code == 401


# ============================================================
# POST /projects/{project_id}/members/{user_id}
# ============================================================


def test_add_project_member(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    member = create_user(
        email="member@example.com",
    )

    owner_token = get_token(owner.email)

    create_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Shared Project"},
    )

    assert create_response.status_code == 201

    project_id = create_response.json()["id"]

    response = client.post(
        f"/projects/{project_id}/members/{member.id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert response.status_code == 201
    assert response.json() == {
        "message": "Member added successfully"
    }


def test_add_project_member_allows_member_to_access_project(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    member = create_user(
        email="member@example.com",
    )

    owner_token = get_token(owner.email)
    member_token = get_token(member.email)

    create_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Shared Project"},
    )

    assert create_response.status_code == 201

    project_id = create_response.json()["id"]

    add_response = client.post(
        f"/projects/{project_id}/members/{member.id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert add_response.status_code == 201

    response = client.get(
        f"/projects/{project_id}",
        headers={"Authorization": f"Bearer {member_token}"},
    )

    assert response.status_code == 200


def test_add_duplicate_project_member(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    member = create_user(
        email="member@example.com",
    )

    owner_token = get_token(owner.email)

    create_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Shared Project"},
    )

    assert create_response.status_code == 201

    project_id = create_response.json()["id"]

    first_response = client.post(
        f"/projects/{project_id}/members/{member.id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert first_response.status_code == 201

    second_response = client.post(
        f"/projects/{project_id}/members/{member.id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "User is already a project member"
    )


def test_add_project_member_project_not_found(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    member = create_user(
        email="member@example.com",
    )

    owner_token = get_token(owner.email)

    response = client.post(
        f"/projects/999999/members/{member.id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_add_project_member_user_not_found(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    owner_token = get_token(owner.email)

    create_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Test Project"},
    )

    assert create_response.status_code == 201

    project_id = create_response.json()["id"]

    response = client.post(
        f"/projects/{project_id}/members/999999",
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_add_project_member_non_owner_forbidden(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    other_user = create_user(
        email="other@example.com",
    )

    member = create_user(
        email="member@example.com",
    )

    owner_token = get_token(owner.email)
    other_token = get_token(other_user.email)

    create_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Owner Project"},
    )

    assert create_response.status_code == 201

    project_id = create_response.json()["id"]

    response = client.post(
        f"/projects/{project_id}/members/{member.id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 403


def test_add_project_member_requires_authentication(
    client: TestClient,
    create_user,
):
    owner = create_user(
        email="owner@example.com",
    )

    response = client.post(
        "/projects/1/members/1",
    )

    assert response.status_code == 401


# ============================================================
# DELETE /projects/{project_id}/members/{user_id}
# ============================================================


def test_remove_project_member(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    member = create_user(
        email="member@example.com",
    )

    owner_token = get_token(owner.email)

    create_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Shared Project"},
    )

    assert create_response.status_code == 201

    project_id = create_response.json()["id"]

    add_response = client.post(
        f"/projects/{project_id}/members/{member.id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert add_response.status_code == 201

    response = client.delete(
        f"/projects/{project_id}/members/{member.id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Member removed successfully"
    }


def test_removed_member_can_no_longer_access_project(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    member = create_user(
        email="member@example.com",
    )

    owner_token = get_token(owner.email)
    member_token = get_token(member.email)

    create_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Shared Project"},
    )

    assert create_response.status_code == 201

    project_id = create_response.json()["id"]

    add_response = client.post(
        f"/projects/{project_id}/members/{member.id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert add_response.status_code == 201

    remove_response = client.delete(
        f"/projects/{project_id}/members/{member.id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert remove_response.status_code == 200

    get_response = client.get(
        f"/projects/{project_id}",
        headers={"Authorization": f"Bearer {member_token}"},
    )

    assert get_response.status_code == 403


def test_remove_project_member_not_found(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    member = create_user(
        email="member@example.com",
    )

    owner_token = get_token(owner.email)

    create_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Test Project"},
    )

    assert create_response.status_code == 201

    project_id = create_response.json()["id"]

    response = client.delete(
        f"/projects/{project_id}/members/{member.id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Project membership not found"
    )


def test_remove_project_member_non_owner_forbidden(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    other_user = create_user(
        email="other@example.com",
    )

    member = create_user(
        email="member@example.com",
    )

    owner_token = get_token(owner.email)
    other_token = get_token(other_user.email)

    create_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Owner Project"},
    )

    assert create_response.status_code == 201

    project_id = create_response.json()["id"]

    add_response = client.post(
        f"/projects/{project_id}/members/{member.id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert add_response.status_code == 201

    response = client.delete(
        f"/projects/{project_id}/members/{member.id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 403


def test_remove_project_member_requires_authentication(
    client: TestClient,
):
    response = client.delete(
        "/projects/1/members/1",
    )

    assert response.status_code == 401


# ============================================================
# ADMIN PROJECT ACCESS
# ============================================================


def test_admin_can_get_any_project(
    client: TestClient,
    create_user,
    get_token,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
    )

    owner = create_user(
        email="owner@example.com",
        role="member",
    )

    owner_token = get_token(owner.email)
    admin_token = get_token(admin.email)

    create_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Owner Project"},
    )

    assert create_response.status_code == 201

    project_id = create_response.json()["id"]

    response = client.get(
        f"/projects/{project_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == project_id
    assert data["name"] == "Owner Project"
    assert data["owner_id"] == owner.id


def test_admin_can_update_any_project(
    client: TestClient,
    create_user,
    get_token,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
    )

    owner = create_user(
        email="owner@example.com",
        role="member",
    )

    owner_token = get_token(owner.email)
    admin_token = get_token(admin.email)

    create_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "name": "Original Project",
            "description": "Original Description",
        },
    )

    assert create_response.status_code == 201

    project_id = create_response.json()["id"]

    response = client.patch(
        f"/projects/{project_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Updated By Admin",
            "description": "Updated By Admin",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Updated By Admin"
    assert data["description"] == "Updated By Admin"
    assert data["owner_id"] == owner.id


def test_admin_can_delete_any_project(
    client: TestClient,
    create_user,
    get_token,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
    )

    owner = create_user(
        email="owner@example.com",
        role="member",
    )

    owner_token = get_token(owner.email)
    admin_token = get_token(admin.email)

    create_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Project To Delete"},
    )

    assert create_response.status_code == 201

    project_id = create_response.json()["id"]

    response = client.delete(
        f"/projects/{project_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 204
    assert response.content == b""


def test_admin_can_add_member_to_any_project(
    client: TestClient,
    create_user,
    get_token,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
    )

    owner = create_user(
        email="owner@example.com",
        role="member",
    )

    member = create_user(
        email="member@example.com",
        role="member",
    )

    owner_token = get_token(owner.email)
    admin_token = get_token(admin.email)

    create_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Owner Project"},
    )

    assert create_response.status_code == 201

    project_id = create_response.json()["id"]

    response = client.post(
        f"/projects/{project_id}/members/{member.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 201
    assert response.json() == {
        "message": "Member added successfully"
    }


def test_admin_can_remove_member_from_any_project(
    client: TestClient,
    create_user,
    get_token,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
    )

    owner = create_user(
        email="owner@example.com",
        role="member",
    )

    member = create_user(
        email="member@example.com",
        role="member",
    )

    owner_token = get_token(owner.email)
    admin_token = get_token(admin.email)

    create_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Owner Project"},
    )

    assert create_response.status_code == 201

    project_id = create_response.json()["id"]

    add_response = client.post(
        f"/projects/{project_id}/members/{member.id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert add_response.status_code == 201

    response = client.delete(
        f"/projects/{project_id}/members/{member.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Member removed successfully"
    }


def test_admin_can_access_project_without_membership(
    client: TestClient,
    create_user,
    get_token,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
    )

    owner = create_user(
        email="owner@example.com",
        role="member",
    )

    admin_token = get_token(admin.email)
    owner_token = get_token(owner.email)

    create_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Private Project"},
    )

    assert create_response.status_code == 201

    project_id = create_response.json()["id"]

    response = client.get(
        f"/projects/{project_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200


def test_admin_can_list_all_projects(
    client: TestClient,
    create_user,
    get_token,
):
    admin = create_user(
        email="admin@example.com",
        role="admin",
    )

    owner1 = create_user(
        email="owner1@example.com",
        role="member",
    )

    owner2 = create_user(
        email="owner2@example.com",
        role="member",
    )

    admin_token = get_token(admin.email)
    owner1_token = get_token(owner1.email)
    owner2_token = get_token(owner2.email)

    response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner1_token}"},
        json={"name": "Project One"},
    )
    assert response.status_code == 201

    response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner2_token}"},
        json={"name": "Project Two"},
    )
    assert response.status_code == 201

    response = client.get(
        "/projects",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert {project["name"] for project in data} == {
        "Project One",
        "Project Two",
    }