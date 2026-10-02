from sqlalchemy import select

from app.db.models import ProjectMember, Task


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


def add_project_member(
    client,
    token,
    project_id,
    user_id,
):
    response = client.post(
        f"/projects/{project_id}/members",
        headers=auth_header(token),
        json={
            "user_id": user_id,
        },
    )

    assert response.status_code == 201

    return response.json()


def create_task(
    client,
    token,
    project_id,
    title="Test Task",
    description="Test Description",
    task_status="todo",
    assignee_id=None,
):
    payload = {
        "title": title,
        "description": description,
        "status": task_status,
    }

    if assignee_id is not None:
        payload["assignee_id"] = assignee_id

    response = client.post(
        f"/projects/{project_id}/tasks",
        headers=auth_header(token),
        json=payload,
    )

    assert response.status_code == 201

    return response.json()


# ============================================================
# CREATE TASK
# ============================================================


def test_create_task_requires_authentication(
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
    )

    response = client.post(
        f"/projects/{project['id']}/tasks",
        json={
            "title": "Task",
        },
    )

    assert response.status_code == 401


def test_admin_can_create_task_in_any_project(
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
    )

    response = client.post(
        f"/projects/{project['id']}/tasks",
        headers=auth_header(admin_token),
        json={
            "title": "Admin Task",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["project_id"] == project["id"]
    assert data["created_by"] == admin.id
    assert data["title"] == "Admin Task"
    assert data["status"] == "todo"


def test_manager_can_create_task_in_own_project(
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
    )

    response = client.post(
        f"/projects/{project['id']}/tasks",
        headers=auth_header(token),
        json={
            "title": "Manager Task",
        },
    )

    assert response.status_code == 201
    assert response.json()["created_by"] == manager.id


def test_manager_cannot_create_task_in_other_manager_project(
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
    )

    response = client.post(
        f"/projects/{project['id']}/tasks",
        headers=auth_header(token1),
        json={
            "title": "Forbidden Task",
        },
    )

    assert response.status_code == 403


def test_manager_member_cannot_create_task_in_other_manager_project(
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
    )

    add_project_member(
        client,
        owner_token,
        project["id"],
        manager.id,
    )

    response = client.post(
        f"/projects/{project['id']}/tasks",
        headers=auth_header(manager_token),
        json={
            "title": "Forbidden Task",
        },
    )

    assert response.status_code == 403


def test_member_cannot_create_task(
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
    )

    add_project_member(
        client,
        manager_token,
        project["id"],
        member.id,
    )

    response = client.post(
        f"/projects/{project['id']}/tasks",
        headers=auth_header(member_token),
        json={
            "title": "Forbidden Task",
        },
    )

    assert response.status_code == 403


def test_create_task_project_not_found(
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
        "/projects/99999/tasks",
        headers=auth_header(token),
        json={
            "title": "Task",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_create_task_title_required(
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
    )

    response = client.post(
        f"/projects/{project['id']}/tasks",
        headers=auth_header(token),
        json={},
    )

    assert response.status_code == 422


def test_create_task_empty_title_rejected(
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
    )

    response = client.post(
        f"/projects/{project['id']}/tasks",
        headers=auth_header(token),
        json={
            "title": "",
        },
    )

    assert response.status_code == 422


def test_create_task_title_over_255_rejected(
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
    )

    response = client.post(
        f"/projects/{project['id']}/tasks",
        headers=auth_header(token),
        json={
            "title": "a" * 256,
        },
    )

    assert response.status_code == 422


def test_create_task_invalid_status_rejected(
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
    )

    response = client.post(
        f"/projects/{project['id']}/tasks",
        headers=auth_header(token),
        json={
            "title": "Task",
            "status": "invalid",
        },
    )

    assert response.status_code == 422


def test_create_task_default_status_is_todo(
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
    )

    response = client.post(
        f"/projects/{project['id']}/tasks",
        headers=auth_header(token),
        json={
            "title": "Task",
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == "todo"


def test_create_task_all_valid_statuses(
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
    )

    for task_status in (
        "todo",
        "in_progress",
        "done",
    ):
        response = client.post(
            f"/projects/{project['id']}/tasks",
            headers=auth_header(token),
            json={
                "title": f"{task_status} task",
                "status": task_status,
            },
        )

        assert response.status_code == 201
        assert response.json()["status"] == task_status


# ============================================================
# ASSIGNEE VALIDATION
# ============================================================


def test_create_task_assignee_must_exist(
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
    )

    response = client.post(
        f"/projects/{project['id']}/tasks",
        headers=auth_header(token),
        json={
            "title": "Task",
            "assignee_id": 99999,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Assignee not found"


def test_create_task_assignee_must_be_project_member(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)
    other_member = create_member(create_user)

    token = get_token(
        manager.email,
        "password123",
    )

    project = create_project(
        client,
        token,
    )

    response = client.post(
        f"/projects/{project['id']}/tasks",
        headers=auth_header(token),
        json={
            "title": "Task",
            "assignee_id": other_member.id,
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Assignee must be a member of the project"
    )


def test_create_task_can_assign_project_member(
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

    project = create_project(
        client,
        manager_token,
    )

    add_project_member(
        client,
        manager_token,
        project["id"],
        member.id,
    )

    response = client.post(
        f"/projects/{project['id']}/tasks",
        headers=auth_header(manager_token),
        json={
            "title": "Assigned Task",
            "assignee_id": member.id,
        },
    )

    assert response.status_code == 201
    assert response.json()["assignee_id"] == member.id


# ============================================================
# LIST TASKS
# ============================================================


def test_list_tasks_requires_authentication(
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
    )

    response = client.get(
        f"/projects/{project['id']}/tasks",
    )

    assert response.status_code == 401


def test_admin_can_list_tasks_from_any_project(
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
    )

    task = create_task(
        client,
        manager_token,
        project["id"],
    )

    response = client.get(
        f"/projects/{project['id']}/tasks",
        headers=auth_header(admin_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == task["id"]


def test_manager_can_list_own_project_tasks(
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
    )

    task = create_task(
        client,
        token,
        project["id"],
    )

    response = client.get(
        f"/projects/{project['id']}/tasks",
        headers=auth_header(token),
    )

    assert response.status_code == 200
    assert response.json()[0]["id"] == task["id"]


def test_manager_can_list_project_tasks_when_member(
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
    )

    task = create_task(
        client,
        owner_token,
        project["id"],
    )

    add_project_member(
        client,
        owner_token,
        project["id"],
        manager.id,
    )

    response = client.get(
        f"/projects/{project['id']}/tasks",
        headers=auth_header(manager_token),
    )

    assert response.status_code == 200
    assert response.json()[0]["id"] == task["id"]


def test_manager_cannot_list_unrelated_project_tasks(
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
    )

    response = client.get(
        f"/projects/{project['id']}/tasks",
        headers=auth_header(token1),
    )

    assert response.status_code == 403


def test_member_can_list_project_tasks(
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
    )

    task = create_task(
        client,
        manager_token,
        project["id"],
    )

    add_project_member(
        client,
        manager_token,
        project["id"],
        member.id,
    )

    response = client.get(
        f"/projects/{project['id']}/tasks",
        headers=auth_header(member_token),
    )

    assert response.status_code == 200
    assert response.json()[0]["id"] == task["id"]


def test_member_cannot_list_unrelated_project_tasks(
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
    )

    response = client.get(
        f"/projects/{project['id']}/tasks",
        headers=auth_header(member_token),
    )

    assert response.status_code == 403


def test_list_tasks_project_not_found(
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
        "/projects/99999/tasks",
        headers=auth_header(token),
    )

    assert response.status_code == 404


def test_list_tasks_filters_by_status(
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
    )

    create_task(
        client,
        token,
        project["id"],
        title="Todo",
        task_status="todo",
    )

    create_task(
        client,
        token,
        project["id"],
        title="In Progress",
        task_status="in_progress",
    )

    response = client.get(
        f"/projects/{project['id']}/tasks?status=in_progress",
        headers=auth_header(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["title"] == "In Progress"


def test_list_tasks_invalid_status_rejected(
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
    )

    response = client.get(
        f"/projects/{project['id']}/tasks?status=invalid",
        headers=auth_header(token),
    )

    assert response.status_code == 422


def test_list_tasks_filters_by_assignee(
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

    project = create_project(
        client,
        manager_token,
    )

    add_project_member(
        client,
        manager_token,
        project["id"],
        member.id,
    )

    create_task(
        client,
        manager_token,
        project["id"],
        title="Assigned",
        assignee_id=member.id,
    )

    create_task(
        client,
        manager_token,
        project["id"],
        title="Unassigned",
    )

    response = client.get(
        f"/projects/{project['id']}/tasks?assignee_id={member.id}",
        headers=auth_header(manager_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["title"] == "Assigned"


def test_list_tasks_pagination(
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
    )

    for index in range(5):
        create_task(
            client,
            token,
            project["id"],
            title=f"Task {index}",
        )

    response = client.get(
        f"/projects/{project['id']}/tasks?page=1&page_size=2",
        headers=auth_header(token),
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_tasks_invalid_page_rejected(
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
    )

    response = client.get(
        f"/projects/{project['id']}/tasks?page=0",
        headers=auth_header(token),
    )

    assert response.status_code == 422


def test_list_tasks_invalid_page_size_rejected(
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
    )

    response = client.get(
        f"/projects/{project['id']}/tasks?page_size=101",
        headers=auth_header(token),
    )

    assert response.status_code == 422


# ============================================================
# GET TASK
# ============================================================


def test_get_task_requires_authentication(
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
    )

    task = create_task(
        client,
        token,
        project["id"],
    )

    response = client.get(
        f"/tasks/{task['id']}",
    )

    assert response.status_code == 401


def test_admin_can_get_any_task(
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
    )

    task = create_task(
        client,
        manager_token,
        project["id"],
    )

    response = client.get(
        f"/tasks/{task['id']}",
        headers=auth_header(admin_token),
    )

    assert response.status_code == 200


def test_manager_can_get_own_project_task(
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
    )

    task = create_task(
        client,
        token,
        project["id"],
    )

    response = client.get(
        f"/tasks/{task['id']}",
        headers=auth_header(token),
    )

    assert response.status_code == 200


def test_manager_can_get_task_from_project_where_member(
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
    )

    task = create_task(
        client,
        owner_token,
        project["id"],
    )

    add_project_member(
        client,
        owner_token,
        project["id"],
        manager.id,
    )

    response = client.get(
        f"/tasks/{task['id']}",
        headers=auth_header(manager_token),
    )

    assert response.status_code == 200


def test_manager_cannot_get_unrelated_task(
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
    )

    task = create_task(
        client,
        token2,
        project["id"],
    )

    response = client.get(
        f"/tasks/{task['id']}",
        headers=auth_header(token1),
    )

    assert response.status_code == 403


def test_member_can_get_task_from_project(
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
    )

    task = create_task(
        client,
        manager_token,
        project["id"],
    )

    add_project_member(
        client,
        manager_token,
        project["id"],
        member.id,
    )

    response = client.get(
        f"/tasks/{task['id']}",
        headers=auth_header(member_token),
    )

    assert response.status_code == 200


def test_member_cannot_get_unrelated_task(
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
    )

    task = create_task(
        client,
        manager_token,
        project["id"],
    )

    response = client.get(
        f"/tasks/{task['id']}",
        headers=auth_header(member_token),
    )

    assert response.status_code == 403


def test_get_task_not_found(
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
        "/tasks/99999",
        headers=auth_header(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


# ============================================================
# UPDATE TASK
# ============================================================


def test_admin_can_update_any_task(
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
    )

    task = create_task(
        client,
        manager_token,
        project["id"],
    )

    response = client.patch(
        f"/tasks/{task['id']}",
        headers=auth_header(admin_token),
        json={
            "title": "Updated By Admin",
        },
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated By Admin"


def test_manager_can_update_task_in_own_project(
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
    )

    task = create_task(
        client,
        token,
        project["id"],
    )

    response = client.patch(
        f"/tasks/{task['id']}",
        headers=auth_header(token),
        json={
            "title": "Updated",
            "description": "Updated Description",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Updated"
    assert data["description"] == "Updated Description"


def test_manager_member_cannot_update_task(
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
    )

    task = create_task(
        client,
        owner_token,
        project["id"],
    )

    add_project_member(
        client,
        owner_token,
        project["id"],
        manager.id,
    )

    response = client.patch(
        f"/tasks/{task['id']}",
        headers=auth_header(manager_token),
        json={
            "title": "Should Fail",
        },
    )

    assert response.status_code == 403


def test_member_cannot_update_task(
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
    )

    task = create_task(
        client,
        manager_token,
        project["id"],
    )

    add_project_member(
        client,
        manager_token,
        project["id"],
        member.id,
    )

    response = client.patch(
        f"/tasks/{task['id']}",
        headers=auth_header(member_token),
        json={
            "title": "Should Fail",
        },
    )

    assert response.status_code == 403


def test_update_task_not_found(
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
        "/tasks/99999",
        headers=auth_header(token),
        json={
            "title": "Updated",
        },
    )

    assert response.status_code == 404


def test_update_task_empty_title_rejected(
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
    )

    task = create_task(
        client,
        token,
        project["id"],
    )

    response = client.patch(
        f"/tasks/{task['id']}",
        headers=auth_header(token),
        json={
            "title": "",
        },
    )

    assert response.status_code == 422


def test_update_task_title_too_long_rejected(
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
    )

    task = create_task(
        client,
        token,
        project["id"],
    )

    response = client.patch(
        f"/tasks/{task['id']}",
        headers=auth_header(token),
        json={
            "title": "a" * 256,
        },
    )

    assert response.status_code == 422


def test_update_task_title_null_rejected(
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
    )

    task = create_task(
        client,
        token,
        project["id"],
    )

    response = client.patch(
        f"/tasks/{task['id']}",
        headers=auth_header(token),
        json={
            "title": None,
        },
    )

    assert response.status_code == 422


def test_update_task_description_can_be_null(
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
    )

    task = create_task(
        client,
        token,
        project["id"],
        description="Description",
    )

    response = client.patch(
        f"/tasks/{task['id']}",
        headers=auth_header(token),
        json={
            "description": None,
        },
    )

    assert response.status_code == 200
    assert response.json()["description"] is None


def test_update_task_assignee_can_be_cleared(
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

    project = create_project(
        client,
        manager_token,
    )

    add_project_member(
        client,
        manager_token,
        project["id"],
        member.id,
    )

    task = create_task(
        client,
        manager_token,
        project["id"],
        assignee_id=member.id,
    )

    response = client.patch(
        f"/tasks/{task['id']}",
        headers=auth_header(manager_token),
        json={
            "assignee_id": None,
        },
    )

    assert response.status_code == 200
    assert response.json()["assignee_id"] is None


def test_update_task_assignee_must_be_project_member(
    client,
    create_user,
    get_token,
):
    manager = create_manager(create_user)
    other_user = create_member(create_user)

    manager_token = get_token(
        manager.email,
        "password123",
    )

    project = create_project(
        client,
        manager_token,
    )

    task = create_task(
        client,
        manager_token,
        project["id"],
    )

    response = client.patch(
        f"/tasks/{task['id']}",
        headers=auth_header(manager_token),
        json={
            "assignee_id": other_user.id,
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Assignee must be a member of the project"
    )


def test_update_task_empty_payload_is_noop(
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
    )

    task = create_task(
        client,
        token,
        project["id"],
        title="Original",
        description="Original Description",
    )

    response = client.patch(
        f"/tasks/{task['id']}",
        headers=auth_header(token),
        json={},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Original"
    assert data["description"] == "Original Description"


# ============================================================
# CHANGE TASK STATUS
# ============================================================


def test_admin_can_change_any_task_status(
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
    )

    task = create_task(
        client,
        manager_token,
        project["id"],
        task_status="todo",
    )

    response = client.patch(
        f"/tasks/{task['id']}/status",
        headers=auth_header(admin_token),
        json={
            "status": "done",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "done"


def test_manager_can_change_status_in_own_project(
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
    )

    task = create_task(
        client,
        token,
        project["id"],
    )

    response = client.patch(
        f"/tasks/{task['id']}/status",
        headers=auth_header(token),
        json={
            "status": "in_progress",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


def test_manager_member_cannot_change_status(
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
    )

    task = create_task(
        client,
        owner_token,
        project["id"],
    )

    add_project_member(
        client,
        owner_token,
        project["id"],
        manager.id,
    )

    response = client.patch(
        f"/tasks/{task['id']}/status",
        headers=auth_header(manager_token),
        json={
            "status": "done",
        },
    )

    assert response.status_code == 403


def test_member_can_change_status(
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
    )

    task = create_task(
        client,
        manager_token,
        project["id"],
    )

    add_project_member(
        client,
        manager_token,
        project["id"],
        member.id,
    )

    response = client.patch(
        f"/tasks/{task['id']}/status",
        headers=auth_header(member_token),
        json={
            "status": "done",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "done"


def test_unrelated_member_cannot_change_status(
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
    )

    task = create_task(
        client,
        manager_token,
        project["id"],
    )

    response = client.patch(
        f"/tasks/{task['id']}/status",
        headers=auth_header(member_token),
        json={
            "status": "done",
        },
    )

    assert response.status_code == 403


def test_change_task_status_not_found(
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
        "/tasks/99999/status",
        headers=auth_header(token),
        json={
            "status": "done",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_change_task_status_invalid_status(
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
    )

    task = create_task(
        client,
        token,
        project["id"],
    )

    response = client.patch(
        f"/tasks/{task['id']}/status",
        headers=auth_header(token),
        json={
            "status": "invalid",
        },
    )

    assert response.status_code == 422


def test_change_task_status_missing_status(
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
    )

    task = create_task(
        client,
        token,
        project["id"],
    )

    response = client.patch(
        f"/tasks/{task['id']}/status",
        headers=auth_header(token),
        json={},
    )

    assert response.status_code == 422


# ============================================================
# DELETE TASK
# ============================================================


def test_admin_can_delete_any_task(
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
    )

    task = create_task(
        client,
        manager_token,
        project["id"],
    )

    response = client.delete(
        f"/tasks/{task['id']}",
        headers=auth_header(admin_token),
    )

    assert response.status_code == 204


def test_manager_can_delete_task_in_own_project(
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
    )

    task = create_task(
        client,
        token,
        project["id"],
    )

    response = client.delete(
        f"/tasks/{task['id']}",
        headers=auth_header(token),
    )

    assert response.status_code == 204


def test_manager_member_cannot_delete_task(
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
    )

    task = create_task(
        client,
        owner_token,
        project["id"],
    )

    add_project_member(
        client,
        owner_token,
        project["id"],
        manager.id,
    )

    response = client.delete(
        f"/tasks/{task['id']}",
        headers=auth_header(manager_token),
    )

    assert response.status_code == 403


def test_member_cannot_delete_task(
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
    )

    task = create_task(
        client,
        manager_token,
        project["id"],
    )

    add_project_member(
        client,
        manager_token,
        project["id"],
        member.id,
    )

    response = client.delete(
        f"/tasks/{task['id']}",
        headers=auth_header(member_token),
    )

    assert response.status_code == 403


def test_delete_task_not_found(
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
        "/tasks/99999",
        headers=auth_header(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


# ============================================================
# DATABASE CONSISTENCY
# ============================================================


def test_create_task_persists(
    client,
    create_user,
    get_token,
    db,
):
    manager = create_manager(create_user)

    token = get_token(
        manager.email,
        "password123",
    )

    project = create_project(
        client,
        token,
    )

    response = client.post(
        f"/projects/{project['id']}/tasks",
        headers=auth_header(token),
        json={
            "title": "Persisted Task",
        },
    )

    assert response.status_code == 201

    task_id = response.json()["id"]

    task = db.get(Task, task_id)

    assert task is not None
    assert task.title == "Persisted Task"
    assert task.project_id == project["id"]
    assert task.created_by == manager.id


def test_delete_task_removes_from_database(
    client,
    create_user,
    get_token,
    db,
):
    manager = create_manager(create_user)

    token = get_token(
        manager.email,
        "password123",
    )

    project = create_project(
        client,
        token,
    )

    task = create_task(
        client,
        token,
        project["id"],
    )

    response = client.delete(
        f"/tasks/{task['id']}",
        headers=auth_header(token),
    )

    assert response.status_code == 204

    deleted_task = db.get(Task, task["id"])

    assert deleted_task is None


def test_update_task_persists(
    client,
    create_user,
    get_token,
    db,
):
    manager = create_manager(create_user)

    token = get_token(
        manager.email,
        "password123",
    )

    project = create_project(
        client,
        token,
    )

    task = create_task(
        client,
        token,
        project["id"],
        title="Original",
    )

    response = client.patch(
        f"/tasks/{task['id']}",
        headers=auth_header(token),
        json={
            "title": "Updated",
        },
    )

    assert response.status_code == 200

    db.expire_all()

    updated_task = db.get(Task, task["id"])

    assert updated_task is not None
    assert updated_task.title == "Updated"


def test_change_task_status_persists(
    client,
    create_user,
    get_token,
    db,
):
    manager = create_manager(create_user)

    token = get_token(
        manager.email,
        "password123",
    )

    project = create_project(
        client,
        token,
    )

    task = create_task(
        client,
        token,
        project["id"],
        task_status="todo",
    )

    response = client.patch(
        f"/tasks/{task['id']}/status",
        headers=auth_header(token),
        json={
            "status": "done",
        },
    )

    assert response.status_code == 200

    db.expire_all()

    updated_task = db.get(Task, task["id"])

    assert updated_task is not None
    assert updated_task.status == "done"