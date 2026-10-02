from sqlalchemy import select

from app.db.models import Project, ProjectMember


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


def create_manager(
    create_user,
    email="manager@example.com",
):
    return create_user(
        email=email,
        role="manager",
        full_name="Manager User",
    )


def create_member(
    create_user,
    email="member@example.com",
):
    return create_user(
        email=email,
        role="member",
        full_name="Member User",
    )


def create_project(
    client,
    token,
    name="Test Project",
    description="Test Description",
):
    response = client.post(
        "/projects",
        headers=auth_header(token),
        json={
            "name": name,
            "description": description,
        },
    )

    assert response.status_code == 201
    return response.json()


def add_member(
    client,
    token,
    project_id,
    user_id,
):
    return client.post(
        f"/projects/{project_id}/members",
        headers=auth_header(token),
        json={
            "user_id": user_id,
        },
    )


# ============================================================
# POST /projects
# ============================================================


def test_create_project_requires_authentication(client):
    response = client.post(
        "/projects",
        json={
            "name": "Test Project",
            "description": "Description",
        },
    )

    assert response.status_code == 401


def test_admin_can_create_project(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)

    token = get_token(
        admin.email,
        "password123",
    )

    response = client.post(
        "/projects",
        headers=auth_header(token),
        json={
            "name": "Admin Project",
            "description": "Created by admin",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Admin Project"
    assert data["description"] == "Created by admin"
    assert data["owner_id"] == admin.id


def test_manager_can_create_project(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)

    token = get_token(
        manager.email,
        "password123",
    )

    response = client.post(
        "/projects",
        headers=auth_header(token),
        json={
            "name": "Manager Project",
            "description": "Created by manager",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["owner_id"] == manager.id


def test_member_cannot_create_project(
    client,
    create_user,
    get_token,
):
    member = create_member(create_user)

    token = get_token(
        member.email,
        "password123",
    )

    response = client.post(
        "/projects",
        headers=auth_header(token),
        json={
            "name": "Member Project",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"


def test_create_project_name_required(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)

    token = get_token(
        manager.email,
        "password123",
    )

    response = client.post(
        "/projects",
        headers=auth_header(token),
        json={},
    )

    assert response.status_code == 422


def test_create_project_empty_name_rejected(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)

    token = get_token(
        manager.email,
        "password123",
    )

    response = client.post(
        "/projects",
        headers=auth_header(token),
        json={
            "name": "",
        },
    )

    assert response.status_code == 422


def test_create_project_name_over_255_rejected(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)

    token = get_token(
        manager.email,
        "password123",
    )

    response = client.post(
        "/projects",
        headers=auth_header(token),
        json={
            "name": "a" * 256,
        },
    )

    assert response.status_code == 422


def test_create_project_description_optional(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)

    token = get_token(
        manager.email,
        "password123",
    )

    response = client.post(
        "/projects",
        headers=auth_header(token),
        json={
            "name": "Project Without Description",
        },
    )

    assert response.status_code == 201
    assert response.json()["description"] is None


# ============================================================
# GET /projects
# ============================================================


def test_list_projects_requires_authentication(client):
    response = client.get("/projects")

    assert response.status_code == 401


def test_admin_can_see_all_projects(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)

    manager1 = create_manager(
        create_user,
        "manager1@example.com",
    )

    manager2 = create_manager(
        create_user,
        "manager2@example.com",
    )

    admin_token = get_token(
        admin.email,
        "password123",
    )

    manager1_token = get_token(
        manager1.email,
        "password123",
    )

    manager2_token = get_token(
        manager2.email,
        "password123",
    )

    project1 = create_project(
        client,
        manager1_token,
        "Project One",
    )

    project2 = create_project(
        client,
        manager2_token,
        "Project Two",
    )

    response = client.get(
        "/projects",
        headers=auth_header(admin_token),
    )

    assert response.status_code == 200

    ids = [project["id"] for project in response.json()]

    assert project1["id"] in ids
    assert project2["id"] in ids


def test_manager_sees_own_projects(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)

    token = get_token(
        manager.email,
        "password123",
    )

    project = create_project(
        client,
        token,
        "Own Project",
    )

    response = client.get(
        "/projects",
        headers=auth_header(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == project["id"]


def test_manager_does_not_see_unrelated_project(
    client,
    create_user,
    get_token,
):
    manager1 = create_manager(
        create_user,
        "manager1@example.com",
    )

    manager2 = create_manager(
        create_user,
        "manager2@example.com",
    )

    token1 = get_token(
        manager1.email,
        "password123",
    )

    token2 = get_token(
        manager2.email,
        "password123",
    )

    project = create_project(
        client,
        token2,
        "Other Project",
    )

    response = client.get(
        "/projects",
        headers=auth_header(token1),
    )

    assert response.status_code == 200

    ids = [item["id"] for item in response.json()]

    assert project["id"] not in ids


def test_member_sees_projects_they_are_member_of(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)

    member = create_member(create_user)

    manager_token = get_token(
        manager.email,
        "password123",
    )

    member_token = get_token(
        member.email,
        "password123",
    )

    project = create_project(
        client,
        manager_token,
        "Member Project",
    )

    response = add_member(
        client,
        manager_token,
        project["id"],
        member.id,
    )

    assert response.status_code == 201

    response = client.get(
        "/projects",
        headers=auth_header(member_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == project["id"]


def test_member_does_not_see_unrelated_projects(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)
    member = create_member(create_user)

    manager_token = get_token(
        manager.email,
        "password123",
    )

    member_token = get_token(
        member.email,
        "password123",
    )

    project = create_project(
        client,
        manager_token,
        "Private Project",
    )

    response = client.get(
        "/projects",
        headers=auth_header(member_token),
    )

    assert response.status_code == 200

    ids = [item["id"] for item in response.json()]

    assert project["id"] not in ids


def test_list_projects_pagination(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)

    token = get_token(
        manager.email,
        "password123",
    )

    for index in range(1, 6):
        create_project(
            client,
            token,
            f"Project {index}",
        )

    response = client.get(
        "/projects?page=1&page_size=2",
        headers=auth_header(token),
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_projects_invalid_page(
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
        "/projects?page=0",
        headers=auth_header(token),
    )

    assert response.status_code == 422


def test_list_projects_invalid_page_size(
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
        "/projects?page_size=101",
        headers=auth_header(token),
    )

    assert response.status_code == 422


# ============================================================
# GET /projects/{project_id}
# ============================================================


def test_get_project_admin_allowed(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)
    manager = create_manager(create_user)

    admin_token = get_token(
        admin.email,
        "password123",
    )

    manager_token = get_token(
        manager.email,
        "password123",
    )

    project = create_project(
        client,
        manager_token,
        "Manager Project",
    )

    response = client.get(
        f"/projects/{project['id']}",
        headers=auth_header(admin_token),
    )

    assert response.status_code == 200
    assert response.json()["id"] == project["id"]


def test_get_project_owner_allowed(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)

    token = get_token(
        manager.email,
        "password123",
    )

    project = create_project(
        client,
        token,
        "Own Project",
    )

    response = client.get(
        f"/projects/{project['id']}",
        headers=auth_header(token),
    )

    assert response.status_code == 200


def test_get_project_member_allowed(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)
    member = create_member(create_user)

    manager_token = get_token(
        manager.email,
        "password123",
    )

    member_token = get_token(
        member.email,
        "password123",
    )

    project = create_project(
        client,
        manager_token,
        "Shared Project",
    )

    response = add_member(
        client,
        manager_token,
        project["id"],
        member.id,
    )

    assert response.status_code == 201

    response = client.get(
        f"/projects/{project['id']}",
        headers=auth_header(member_token),
    )

    assert response.status_code == 200


def test_get_project_unrelated_manager_forbidden(
    client,
    create_user,
    get_token,
):
    manager1 = create_manager(
        create_user,
        "manager1@example.com",
    )

    manager2 = create_manager(
        create_user,
        "manager2@example.com",
    )

    token1 = get_token(
        manager1.email,
        "password123",
    )

    token2 = get_token(
        manager2.email,
        "password123",
    )

    project = create_project(
        client,
        token2,
        "Other Project",
    )

    response = client.get(
        f"/projects/{project['id']}",
        headers=auth_header(token1),
    )

    assert response.status_code == 403


def test_get_project_unrelated_member_forbidden(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)
    member = create_member(create_user)

    manager_token = get_token(
        manager.email,
        "password123",
    )

    member_token = get_token(
        member.email,
        "password123",
    )

    project = create_project(
        client,
        manager_token,
        "Private Project",
    )

    response = client.get(
        f"/projects/{project['id']}",
        headers=auth_header(member_token),
    )

    assert response.status_code == 403


def test_get_project_not_found(
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
        "/projects/99999",
        headers=auth_header(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


# ============================================================
# PATCH /projects/{project_id}
# ============================================================


def test_update_project_admin_allowed(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)

    manager = create_manager(create_user)

    admin_token = get_token(
        admin.email,
        "password123",
    )

    manager_token = get_token(
        manager.email,
        "password123",
    )

    project = create_project(
        client,
        manager_token,
        "Original",
        "Original Description",
    )

    response = client.patch(
        f"/projects/{project['id']}",
        headers=auth_header(admin_token),
        json={
            "name": "Updated By Admin",
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated By Admin"


def test_update_project_owner_allowed(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)

    token = get_token(
        manager.email,
        "password123",
    )

    project = create_project(
        client,
        token,
        "Original",
        "Original Description",
    )

    response = client.patch(
        f"/projects/{project['id']}",
        headers=auth_header(token),
        json={
            "name": "Updated",
            "description": "Updated Description",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Updated"
    assert data["description"] == "Updated Description"


def test_manager_member_cannot_update_project(
    client,
    create_user,
    get_token,
):
    owner = create_manager(
        create_user,
        "owner@example.com",
    )

    manager = create_manager(
        create_user,
        "manager@example.com",
    )

    owner_token = get_token(
        owner.email,
        "password123",
    )

    manager_token = get_token(
        manager.email,
        "password123",
    )

    project = create_project(
        client,
        owner_token,
        "Original",
    )

    response = add_member(
        client,
        owner_token,
        project["id"],
        manager.id,
    )

    assert response.status_code == 201

    response = client.patch(
        f"/projects/{project['id']}",
        headers=auth_header(manager_token),
        json={
            "name": "Should Fail",
        },
    )

    assert response.status_code == 403


def test_member_cannot_update_project(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)
    member = create_member(create_user)

    manager_token = get_token(
        manager.email,
        "password123",
    )

    member_token = get_token(
        member.email,
        "password123",
    )

    project = create_project(
        client,
        manager_token,
        "Original",
    )

    response = add_member(
        client,
        manager_token,
        project["id"],
        member.id,
    )

    assert response.status_code == 201

    response = client.patch(
        f"/projects/{project['id']}",
        headers=auth_header(member_token),
        json={
            "name": "Should Fail",
        },
    )

    assert response.status_code == 403


def test_update_project_not_found(
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
        "/projects/99999",
        headers=auth_header(token),
        json={
            "name": "Updated",
        },
    )

    assert response.status_code == 404


def test_update_project_empty_name_rejected(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)

    token = get_token(
        manager.email,
        "password123",
    )

    project = create_project(
        client,
        token,
        "Original",
    )

    response = client.patch(
        f"/projects/{project['id']}",
        headers=auth_header(token),
        json={
            "name": "",
        },
    )

    assert response.status_code == 422


def test_update_project_name_over_255_rejected(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)

    token = get_token(
        manager.email,
        "password123",
    )

    project = create_project(
        client,
        token,
        "Original",
    )

    response = client.patch(
        f"/projects/{project['id']}",
        headers=auth_header(token),
        json={
            "name": "a" * 256,
        },
    )

    assert response.status_code == 422


def test_update_project_can_clear_description(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)

    token = get_token(
        manager.email,
        "password123",
    )

    project = create_project(
        client,
        token,
        "Project",
        "Description",
    )

    response = client.patch(
        f"/projects/{project['id']}",
        headers=auth_header(token),
        json={
            "description": None,
        },
    )

    assert response.status_code == 200
    assert response.json()["description"] is None


def test_update_project_name_null_is_accepted_as_no_name_change(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)

    token = get_token(
        manager.email,
        "password123",
    )

    project = create_project(
        client,
        token,
        "Original",
        "Description",
    )

    response = client.patch(
        f"/projects/{project['id']}",
        headers=auth_header(token),
        json={
            "name": None,
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Original"


def test_update_project_empty_payload_is_noop(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)

    token = get_token(
        manager.email,
        "password123",
    )

    project = create_project(
        client,
        token,
        "Original",
        "Description",
    )

    response = client.patch(
        f"/projects/{project['id']}",
        headers=auth_header(token),
        json={},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Original"
    assert data["description"] == "Description"


# ============================================================
# DELETE /projects/{project_id}
# ============================================================


def test_delete_project_requires_owner(
    client,
    create_user,
    get_token,
):
    manager1 = create_manager(
        create_user,
        "manager1@example.com",
    )

    manager2 = create_manager(
        create_user,
        "manager2@example.com",
    )

    token1 = get_token(
        manager1.email,
        "password123",
    )

    token2 = get_token(
        manager2.email,
        "password123",
    )

    project = create_project(
        client,
        token2,
        "Other Project",
    )

    response = client.delete(
        f"/projects/{project['id']}",
        headers=auth_header(token1),
    )

    assert response.status_code == 403

    response = client.delete(
        f"/projects/{project['id']}",
        headers=auth_header(token2),
    )

    assert response.status_code == 204


def test_admin_can_delete_any_project(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)
    manager = create_manager(create_user)

    admin_token = get_token(
        admin.email,
        "password123",
    )

    manager_token = get_token(
        manager.email,
        "password123",
    )

    project = create_project(
        client,
        manager_token,
        "Project",
    )

    response = client.delete(
        f"/projects/{project['id']}",
        headers=auth_header(admin_token),
    )

    assert response.status_code == 204

    response = client.get(
        f"/projects/{project['id']}",
        headers=auth_header(admin_token),
    )

    assert response.status_code == 404


def test_member_cannot_delete_project(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)
    member = create_member(create_user)

    manager_token = get_token(
        manager.email,
        "password123",
    )

    member_token = get_token(
        member.email,
        "password123",
    )

    project = create_project(
        client,
        manager_token,
        "Project",
    )

    response = add_member(
        client,
        manager_token,
        project["id"],
        member.id,
    )

    assert response.status_code == 201

    response = client.delete(
        f"/projects/{project['id']}",
        headers=auth_header(member_token),
    )

    assert response.status_code == 403


def test_delete_project_not_found(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)

    token = get_token(
        admin.email,
        "password123",
    )

    response = client.delete(
        "/projects/99999",
        headers=auth_header(token),
    )

    assert response.status_code == 404


# ============================================================
# POST /projects/{project_id}/members
# ============================================================


def test_add_member_requires_authentication(
    client,
    create_user,
):
    manager = create_manager(create_user)

    # No authenticated request.
    response = client.post(
        "/projects/1/members",
        json={
            "user_id": manager.id,
        },
    )

    assert response.status_code == 401


def test_project_owner_can_add_member(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)
    member = create_member(create_user)

    token = get_token(
        manager.email,
        "password123",
    )

    project = create_project(
        client,
        token,
        "Project",
    )

    response = add_member(
        client,
        token,
        project["id"],
        member.id,
    )

    assert response.status_code == 201
    assert response.json()["message"] == "Member added successfully"


def test_admin_can_add_member_to_any_project(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)
    manager = create_manager(create_user)
    member = create_member(create_user)

    admin_token = get_token(
        admin.email,
        "password123",
    )

    manager_token = get_token(
        manager.email,
        "password123",
    )

    project = create_project(
        client,
        manager_token,
        "Manager Project",
    )

    response = add_member(
        client,
        admin_token,
        project["id"],
        member.id,
    )

    assert response.status_code == 201


def test_manager_member_cannot_add_member(
    client,
    create_user,
    get_token,
):
    owner = create_manager(
        create_user,
        "owner@example.com",
    )

    manager = create_manager(
        create_user,
        "manager@example.com",
    )

    target = create_member(
        create_user,
        "target@example.com",
    )

    owner_token = get_token(
        owner.email,
        "password123",
    )

    manager_token = get_token(
        manager.email,
        "password123",
    )

    project = create_project(
        client,
        owner_token,
        "Project",
    )

    response = add_member(
        client,
        owner_token,
        project["id"],
        manager.id,
    )

    assert response.status_code == 201

    response = add_member(
        client,
        manager_token,
        project["id"],
        target.id,
    )

    assert response.status_code == 403


def test_member_cannot_add_member(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)
    member1 = create_member(
        create_user,
        "member1@example.com",
    )
    member2 = create_member(
        create_user,
        "member2@example.com",
    )

    manager_token = get_token(
        manager.email,
        "password123",
    )

    member1_token = get_token(
        member1.email,
        "password123",
    )

    project = create_project(
        client,
        manager_token,
        "Project",
    )

    response = add_member(
        client,
        manager_token,
        project["id"],
        member1.id,
    )

    assert response.status_code == 201

    response = add_member(
        client,
        member1_token,
        project["id"],
        member2.id,
    )

    assert response.status_code == 403


def test_add_member_target_user_not_found(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)

    token = get_token(
        manager.email,
        "password123",
    )

    project = create_project(
        client,
        token,
        "Project",
    )

    response = add_member(
        client,
        token,
        project["id"],
        99999,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_add_member_project_not_found(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)
    member = create_member(create_user)

    token = get_token(
        manager.email,
        "password123",
    )

    response = add_member(
        client,
        token,
        99999,
        member.id,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_add_member_duplicate_rejected(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)
    member = create_member(create_user)

    token = get_token(
        manager.email,
        "password123",
    )

    project = create_project(
        client,
        token,
        "Project",
    )

    response = add_member(
        client,
        token,
        project["id"],
        member.id,
    )

    assert response.status_code == 201

    response = add_member(
        client,
        token,
        project["id"],
        member.id,
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "User is already a project member"
    )


def test_add_member_missing_user_id(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)

    token = get_token(
        manager.email,
        "password123",
    )

    project = create_project(
        client,
        token,
        "Project",
    )

    response = client.post(
        f"/projects/{project['id']}/members",
        headers=auth_header(token),
        json={},
    )

    assert response.status_code == 422


def test_add_member_invalid_user_id(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)

    token = get_token(
        manager.email,
        "password123",
    )

    project = create_project(
        client,
        token,
        "Project",
    )

    response = client.post(
        f"/projects/{project['id']}/members",
        headers=auth_header(token),
        json={
            "user_id": "invalid",
        },
    )

    assert response.status_code == 422


# ============================================================
# DELETE /projects/{project_id}/members/{user_id}
# ============================================================


def test_remove_member_project_owner_allowed(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)
    member = create_member(create_user)

    token = get_token(
        manager.email,
        "password123",
    )

    project = create_project(
        client,
        token,
        "Project",
    )

    response = add_member(
        client,
        token,
        project["id"],
        member.id,
    )

    assert response.status_code == 201

    response = client.delete(
        f"/projects/{project['id']}/members/{member.id}",
        headers=auth_header(token),
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Member removed successfully"


def test_remove_member_admin_allowed(
    client,
    create_user,
    get_token,
):
    admin = create_admin(create_user)
    manager = create_manager(create_user)
    member = create_member(create_user)

    admin_token = get_token(
        admin.email,
        "password123",
    )

    manager_token = get_token(
        manager.email,
        "password123",
    )

    project = create_project(
        client,
        manager_token,
        "Project",
    )

    response = add_member(
        client,
        manager_token,
        project["id"],
        member.id,
    )

    assert response.status_code == 201

    response = client.delete(
        f"/projects/{project['id']}/members/{member.id}",
        headers=auth_header(admin_token),
    )

    assert response.status_code == 200


def test_manager_member_cannot_remove_member(
    client,
    create_user,
    get_token,
):
    owner = create_manager(
        create_user,
        "owner@example.com",
    )

    manager = create_manager(
        create_user,
        "manager@example.com",
    )

    target = create_member(
        create_user,
        "target@example.com",
    )

    owner_token = get_token(
        owner.email,
        "password123",
    )

    manager_token = get_token(
        manager.email,
        "password123",
    )

    project = create_project(
        client,
        owner_token,
        "Project",
    )

    response = add_member(
        client,
        owner_token,
        project["id"],
        manager.id,
    )

    assert response.status_code == 201

    response = add_member(
        client,
        owner_token,
        project["id"],
        target.id,
    )

    assert response.status_code == 201

    response = client.delete(
        f"/projects/{project['id']}/members/{target.id}",
        headers=auth_header(manager_token),
    )

    assert response.status_code == 403


def test_member_cannot_remove_member(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)
    member1 = create_member(
        create_user,
        "member1@example.com",
    )
    member2 = create_member(
        create_user,
        "member2@example.com",
    )

    manager_token = get_token(
        manager.email,
        "password123",
    )

    member1_token = get_token(
        member1.email,
        "password123",
    )

    project = create_project(
        client,
        manager_token,
        "Project",
    )

    response = add_member(
        client,
        manager_token,
        project["id"],
        member1.id,
    )

    assert response.status_code == 201

    response = add_member(
        client,
        manager_token,
        project["id"],
        member2.id,
    )

    assert response.status_code == 201

    response = client.delete(
        f"/projects/{project['id']}/members/{member2.id}",
        headers=auth_header(member1_token),
    )

    assert response.status_code == 403


def test_remove_member_not_found(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)
    member = create_member(create_user)

    token = get_token(
        manager.email,
        "password123",
    )

    project = create_project(
        client,
        token,
        "Project",
    )

    response = client.delete(
        f"/projects/{project['id']}/members/{member.id}",
        headers=auth_header(token),
    )

    assert response.status_code == 404
    assert (
        response.json()["detail"]
        == "Project membership not found"
    )


def test_remove_member_project_not_found(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)
    member = create_member(create_user)

    token = get_token(
        manager.email,
        "password123",
    )

    response = client.delete(
        f"/projects/99999/members/{member.id}",
        headers=auth_header(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


# ============================================================
# DATABASE MEMBERSHIP CONSISTENCY
# ============================================================


def test_add_member_creates_membership(
    client,
    create_user,
    get_token,
    db,
):
    manager = create_manager(create_user)
    member = create_member(create_user)

    token = get_token(
        manager.email,
        "password123",
    )

    project = create_project(
        client,
        token,
        "Project",
    )

    response = add_member(
        client,
        token,
        project["id"],
        member.id,
    )

    assert response.status_code == 201

    membership = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project["id"],
            ProjectMember.user_id == member.id,
        )
    )

    assert membership is not None


def test_remove_member_deletes_membership(
    client,
    create_user,
    get_token,
    db,
):
    manager = create_manager(create_user)
    member = create_member(create_user)

    token = get_token(
        manager.email,
        "password123",
    )

    project = create_project(
        client,
        token,
        "Project",
    )

    response = add_member(
        client,
        token,
        project["id"],
        member.id,
    )

    assert response.status_code == 201

    response = client.delete(
        f"/projects/{project['id']}/members/{member.id}",
        headers=auth_header(token),
    )

    assert response.status_code == 200

    membership = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project["id"],
            ProjectMember.user_id == member.id,
        )
    )

    assert membership is None