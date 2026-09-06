from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import Base, app, get_db

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)

Base.metadata.create_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_home():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "DevOps project is running!"
    }


def test_get_tasks():
    response = client.get("/tasks")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_task():
    task = {
        "title": "Test Task",
        "description": "Created by pytest",
    }

    response = client.post("/tasks", json=task)

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Test Task"
    assert data["description"] == "Created by pytest"
    assert "id" in data


def test_get_task():
    response = client.post(
        "/tasks",
        json={
            "title": "Task for GET",
            "description": "Testing GET endpoint",
        },
    )

    task_id = response.json()["id"]

    response = client.get(f"/tasks/{task_id}")

    assert response.status_code == 200
    assert response.json()["id"] == task_id


def test_get_task_not_found():
    response = client.get("/tasks/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_update_task():
    response = client.post(
        "/tasks",
        json={
            "title": "Old Title",
            "description": "Old Description",
        },
    )

    task_id = response.json()["id"]

    response = client.put(
        f"/tasks/{task_id}",
        json={
            "title": "Updated Title",
            "description": "Updated Description",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == task_id
    assert data["title"] == "Updated Title"
    assert data["description"] == "Updated Description"


def test_update_task_not_found():
    response = client.put(
        "/tasks/999999",
        json={
            "title": "Updated",
            "description": "Updated",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_delete_task():
    response = client.post(
        "/tasks",
        json={
            "title": "Task to Delete",
            "description": "Will be deleted",
        },
    )

    task_id = response.json()["id"]

    response = client.delete(f"/tasks/{task_id}")

    assert response.status_code == 200
    assert response.json()["message"] == "Task deleted successfully"

    response = client.get(f"/tasks/{task_id}")

    assert response.status_code == 404


def test_delete_task_not_found():
    response = client.delete("/tasks/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"