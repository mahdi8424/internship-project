import pytest
from fastapi.testclient import TestClient


# ============================================================
# CREATE TASK
# ============================================================


def test_create_task_as_project_owner(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    token = get_token(owner.email)

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Test Project",
            "description": "Project description",
        },
    )

    assert project_response.status_code == 201

    project_id = project_response.json()["id"]

    response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Test Task",
            "description": "Task description",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["project_id"] == project_id
    assert data["title"] == "Test Task"
    assert data["description"] == "Task description"
    assert data["status"] == "todo"
    assert data["assignee_id"] is None
    assert data["created_by"] == owner.id


def test_create_task_as_project_member(
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

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Test Project"},
    )

    assert project_response.status_code == 201

    project_id = project_response.json()["id"]

    add_response = client.post(
        f"/projects/{project_id}/members/{member.id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert add_response.status_code == 201

    response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {member_token}"},
        json={"title": "Member Task"},
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "Member Task"
    assert data["created_by"] == member.id


def test_create_task_as_admin(
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
    )

    admin_token = get_token(admin.email)
    owner_token = get_token(owner.email)

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Owner Project"},
    )

    assert project_response.status_code == 201

    project_id = project_response.json()["id"]

    response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"title": "Admin Task"},
    )

    assert response.status_code == 201

    data = response.json()

    assert data["project_id"] == project_id
    assert data["title"] == "Admin Task"
    assert data["created_by"] == admin.id


def test_create_task_as_non_member_forbidden(
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

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Private Project"},
    )

    assert project_response.status_code == 201

    project_id = project_response.json()["id"]

    response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {other_token}"},
        json={"title": "Forbidden Task"},
    )

    assert response.status_code == 403


def test_create_task_project_not_found(
    client: TestClient,
    create_user,
    get_token,
):
    user = create_user(
        email="user@example.com",
    )

    token = get_token(user.email)

    response = client.post(
        "/projects/99999/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Test Task"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


# ============================================================
# CREATE TASK VALIDATION
# ============================================================


@pytest.mark.parametrize(
    "payload",
    [
        {"title": ""},
        {"title": "a" * 256},
    ],
)
def test_create_task_invalid_title(
    client: TestClient,
    create_user,
    get_token,
    payload,
):
    owner = create_user(
        email="owner@example.com",
    )

    token = get_token(owner.email)

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Test Project"},
    )

    assert project_response.status_code == 201

    project_id = project_response.json()["id"]

    response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "task_status",
    [
        "todo",
        "in_progress",
        "done",
    ],
)
def test_create_task_valid_status(
    client: TestClient,
    create_user,
    get_token,
    task_status,
):
    owner = create_user(
        email="owner@example.com",
    )

    token = get_token(owner.email)

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Test Project"},
    )

    assert project_response.status_code == 201

    project_id = project_response.json()["id"]

    response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Test Task",
            "status": task_status,
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == task_status


def test_create_task_invalid_status(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    token = get_token(owner.email)

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Test Project"},
    )

    assert project_response.status_code == 201

    project_id = project_response.json()["id"]

    response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Test Task",
            "status": "invalid",
        },
    )

    assert response.status_code == 422


# ============================================================
# ASSIGNEE VALIDATION
# ============================================================


def test_create_task_with_project_member_assignee(
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

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Test Project"},
    )

    assert project_response.status_code == 201

    project_id = project_response.json()["id"]

    add_response = client.post(
        f"/projects/{project_id}/members/{member.id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert add_response.status_code == 201

    response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "title": "Assigned Task",
            "assignee_id": member.id,
        },
    )

    assert response.status_code == 201
    assert response.json()["assignee_id"] == member.id


def test_create_task_with_nonexistent_assignee(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    token = get_token(owner.email)

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Test Project"},
    )

    assert project_response.status_code == 201

    project_id = project_response.json()["id"]

    response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Assigned Task",
            "assignee_id": 99999,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Assignee not found"


def test_create_task_with_non_member_assignee(
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

    token = get_token(owner.email)

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Test Project"},
    )

    assert project_response.status_code == 201

    project_id = project_response.json()["id"]

    response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Assigned Task",
            "assignee_id": other_user.id,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Assignee must be a member of the project"
    )


# ============================================================
# LIST TASKS
# ============================================================


def test_list_tasks_as_owner(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    token = get_token(owner.email)

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Test Project"},
    )

    project_id = project_response.json()["id"]

    for title in ["Task 1", "Task 2", "Task 3"]:
        response = client.post(
            f"/projects/{project_id}/tasks",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": title},
        )
        assert response.status_code == 201

    response = client.get(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 3
    assert [task["title"] for task in data] == [
        "Task 1",
        "Task 2",
        "Task 3",
    ]


def test_list_tasks_as_member(
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

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Test Project"},
    )

    project_id = project_response.json()["id"]

    add_response = client.post(
        f"/projects/{project_id}/members/{member.id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert add_response.status_code == 201

    create_response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"title": "Member Visible Task"},
    )

    assert create_response.status_code == 201

    response = client.get(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {member_token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_list_tasks_as_admin(
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
    )

    admin_token = get_token(admin.email)
    owner_token = get_token(owner.email)

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Owner Project"},
    )

    project_id = project_response.json()["id"]

    create_response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"title": "Admin Visible Task"},
    )

    assert create_response.status_code == 201

    response = client.get(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_list_tasks_non_member_forbidden(
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

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Private Project"},
    )

    project_id = project_response.json()["id"]

    response = client.get(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 403


# ============================================================
# LIST TASKS FILTERING
# ============================================================


def test_list_tasks_filter_by_status(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    token = get_token(owner.email)

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Test Project"},
    )

    project_id = project_response.json()["id"]

    for title, task_status in [
        ("Todo Task", "todo"),
        ("Progress Task", "in_progress"),
        ("Done Task", "done"),
    ]:
        response = client.post(
            f"/projects/{project_id}/tasks",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": title,
                "status": task_status,
            },
        )
        assert response.status_code == 201

    response = client.get(
        f"/projects/{project_id}/tasks?status=done",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["title"] == "Done Task"
    assert data[0]["status"] == "done"


def test_list_tasks_filter_by_assignee(
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

    token = get_token(owner.email)

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Test Project"},
    )

    project_id = project_response.json()["id"]

    add_response = client.post(
        f"/projects/{project_id}/members/{member.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert add_response.status_code == 201

    response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Assigned Task",
            "assignee_id": member.id,
        },
    )

    assert response.status_code == 201

    response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Unassigned Task"},
    )

    assert response.status_code == 201

    response = client.get(
        f"/projects/{project_id}/tasks?assignee_id={member.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["title"] == "Assigned Task"
    assert data[0]["assignee_id"] == member.id


# ============================================================
# TASK PAGINATION
# ============================================================


def test_list_tasks_pagination(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    token = get_token(owner.email)

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Test Project"},
    )

    project_id = project_response.json()["id"]

    for number in range(1, 6):
        response = client.post(
            f"/projects/{project_id}/tasks",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": f"Task {number}"},
        )
        assert response.status_code == 201

    response = client.get(
        f"/projects/{project_id}/tasks?page=1&page_size=2",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert [task["title"] for task in data] == [
        "Task 1",
        "Task 2",
    ]

    response = client.get(
        f"/projects/{project_id}/tasks?page=2&page_size=2",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert [task["title"] for task in data] == [
        "Task 3",
        "Task 4",
    ]


@pytest.mark.parametrize(
    "query",
    [
        "?page=0",
        "?page=-1",
        "?page_size=0",
        "?page_size=101",
    ],
)
def test_list_tasks_invalid_pagination(
    client: TestClient,
    create_user,
    get_token,
    query,
):
    owner = create_user(
        email="owner@example.com",
    )

    token = get_token(owner.email)

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Test Project"},
    )

    project_id = project_response.json()["id"]

    response = client.get(
        f"/projects/{project_id}/tasks{query}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


# ============================================================
# GET TASK
# ============================================================


def test_get_task_as_owner(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    token = get_token(owner.email)

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Test Project"},
    )

    project_id = project_response.json()["id"]

    create_response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Test Task"},
    )

    task_id = create_response.json()["id"]

    response = client.get(
        f"/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == task_id
    assert response.json()["title"] == "Test Task"


def test_get_task_as_member(
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

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Test Project"},
    )

    project_id = project_response.json()["id"]

    add_response = client.post(
        f"/projects/{project_id}/members/{member.id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert add_response.status_code == 201

    create_response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"title": "Member Task"},
    )

    task_id = create_response.json()["id"]

    response = client.get(
        f"/tasks/{task_id}",
        headers={"Authorization": f"Bearer {member_token}"},
    )

    assert response.status_code == 200


def test_get_task_as_admin(
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
    )

    admin_token = get_token(admin.email)
    owner_token = get_token(owner.email)

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Owner Project"},
    )

    project_id = project_response.json()["id"]

    create_response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"title": "Admin Task"},
    )

    task_id = create_response.json()["id"]

    response = client.get(
        f"/tasks/{task_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200


def test_get_task_non_member_forbidden(
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

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Private Project"},
    )

    project_id = project_response.json()["id"]

    create_response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"title": "Private Task"},
    )

    task_id = create_response.json()["id"]

    response = client.get(
        f"/tasks/{task_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 403


def test_get_task_not_found(
    client: TestClient,
    create_user,
    get_token,
):
    user = create_user(
        email="user@example.com",
    )

    token = get_token(user.email)

    response = client.get(
        "/tasks/99999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


# ============================================================
# UPDATE TASK
# ============================================================


def test_update_task_as_owner(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    token = get_token(owner.email)

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Test Project"},
    )

    project_id = project_response.json()["id"]

    create_response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Original",
            "description": "Original description",
        },
    )

    task_id = create_response.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Updated",
            "description": "Updated description",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Updated"
    assert data["description"] == "Updated description"


def test_update_task_as_admin(
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
    )

    admin_token = get_token(admin.email)
    owner_token = get_token(owner.email)

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Owner Project"},
    )

    project_id = project_response.json()["id"]

    create_response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"title": "Original"},
    )

    task_id = create_response.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"title": "Updated By Admin"},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated By Admin"


def test_update_task_as_non_member_forbidden(
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

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Private Project"},
    )

    project_id = project_response.json()["id"]

    create_response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"title": "Private Task"},
    )

    task_id = create_response.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}",
        headers={"Authorization": f"Bearer {other_token}"},
        json={"title": "Hacked"},
    )

    assert response.status_code == 403


@pytest.mark.parametrize(
    "payload",
    [
        {"title": ""},
        {"title": "a" * 256},
    ],
)
def test_update_task_invalid_title(
    client: TestClient,
    create_user,
    get_token,
    payload,
):
    owner = create_user(
        email="owner@example.com",
    )

    token = get_token(owner.email)

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Test Project"},
    )

    project_id = project_response.json()["id"]

    create_response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Original"},
    )

    task_id = create_response.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )

    assert response.status_code == 422


def test_update_task_null_title_rejected(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(email="owner@example.com")
    token = get_token(owner.email)

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Test Project"},
    )

    assert project_response.status_code == 201

    project_id = project_response.json()["id"]

    create_response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Original"},
    )

    assert create_response.status_code == 201

    task_id = create_response.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": None},
    )

    assert response.status_code == 422


# ============================================================
# UPDATE TASK ASSIGNEE
# ============================================================


def test_update_task_assignee(
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

    token = get_token(owner.email)

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Test Project"},
    )

    project_id = project_response.json()["id"]

    add_response = client.post(
        f"/projects/{project_id}/members/{member.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert add_response.status_code == 201

    create_response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Task"},
    )

    task_id = create_response.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"assignee_id": member.id},
    )

    assert response.status_code == 200
    assert response.json()["assignee_id"] == member.id


def test_update_task_assignee_to_non_member_fails(
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

    token = get_token(owner.email)

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Test Project"},
    )

    project_id = project_response.json()["id"]

    create_response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Task"},
    )

    task_id = create_response.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"assignee_id": other_user.id},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Assignee must be a member of the project"
    )


def test_update_task_assignee_to_nonexistent_user_fails(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    token = get_token(owner.email)

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Test Project"},
    )

    project_id = project_response.json()["id"]

    create_response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Task"},
    )

    task_id = create_response.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"assignee_id": 99999},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Assignee not found"


def test_update_task_unassign(
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

    token = get_token(owner.email)

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Test Project"},
    )

    project_id = project_response.json()["id"]

    add_response = client.post(
        f"/projects/{project_id}/members/{member.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert add_response.status_code == 201

    create_response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Assigned Task",
            "assignee_id": member.id,
        },
    )

    task_id = create_response.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"assignee_id": None},
    )

    assert response.status_code == 200
    assert response.json()["assignee_id"] is None


# ============================================================
# UPDATE TASK STATUS
# ============================================================


@pytest.mark.parametrize(
    "task_status",
    [
        "todo",
        "in_progress",
        "done",
    ],
)
def test_update_task_status(
    client: TestClient,
    create_user,
    get_token,
    task_status,
):
    owner = create_user(
        email="owner@example.com",
    )

    token = get_token(owner.email)

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Test Project"},
    )

    project_id = project_response.json()["id"]

    create_response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Task"},
    )

    task_id = create_response.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": task_status},
    )

    assert response.status_code == 200
    assert response.json()["status"] == task_status


def test_update_task_status_invalid(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    token = get_token(owner.email)

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Test Project"},
    )

    project_id = project_response.json()["id"]

    create_response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Task"},
    )

    task_id = create_response.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "invalid"},
    )

    assert response.status_code == 422


def test_update_task_status_as_admin(
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
    )

    admin_token = get_token(admin.email)
    owner_token = get_token(owner.email)

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Owner Project"},
    )

    project_id = project_response.json()["id"]

    create_response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"title": "Task"},
    )

    task_id = create_response.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "done"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "done"


def test_update_task_status_non_member_forbidden(
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

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Private Project"},
    )

    project_id = project_response.json()["id"]

    create_response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"title": "Private Task"},
    )

    task_id = create_response.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}/status",
        headers={"Authorization": f"Bearer {other_token}"},
        json={"status": "done"},
    )

    assert response.status_code == 403


# ============================================================
# DELETE TASK
# ============================================================


def test_delete_task_as_owner(
    client: TestClient,
    create_user,
    get_token,
):
    owner = create_user(
        email="owner@example.com",
    )

    token = get_token(owner.email)

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Test Project"},
    )

    project_id = project_response.json()["id"]

    create_response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Task To Delete"},
    )

    task_id = create_response.json()["id"]

    response = client.delete(
        f"/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204
    assert response.content == b""

    response = client.get(
        f"/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


def test_delete_task_as_member(
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

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Test Project"},
    )

    project_id = project_response.json()["id"]

    add_response = client.post(
        f"/projects/{project_id}/members/{member.id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert add_response.status_code == 201

    create_response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"title": "Task To Delete"},
    )

    task_id = create_response.json()["id"]

    response = client.delete(
        f"/tasks/{task_id}",
        headers={"Authorization": f"Bearer {member_token}"},
    )

    assert response.status_code == 204


def test_delete_task_as_admin(
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
    )

    admin_token = get_token(admin.email)
    owner_token = get_token(owner.email)

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Owner Project"},
    )

    project_id = project_response.json()["id"]

    create_response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"title": "Admin Delete Task"},
    )

    task_id = create_response.json()["id"]

    response = client.delete(
        f"/tasks/{task_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 204


def test_delete_task_non_member_forbidden(
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

    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Private Project"},
    )

    project_id = project_response.json()["id"]

    create_response = client.post(
        f"/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"title": "Private Task"},
    )

    task_id = create_response.json()["id"]

    response = client.delete(
        f"/tasks/{task_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 403


def test_delete_task_not_found(
    client: TestClient,
    create_user,
    get_token,
):
    user = create_user(
        email="user@example.com",
    )

    token = get_token(user.email)

    response = client.delete(
        "/tasks/99999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"