import pytest
from litestar.testing import TestClient
from yoyo import get_backend, read_migrations


@pytest.fixture
def client(tmp_path):

    db_file = tmp_path / "test_db.sqlite"
    db_url = f"sqlite:///{db_file}"

    backend = get_backend(db_url)
    migrations = read_migrations("./migrations")
    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))

    from app import create_app

    test_app = create_app(debug=False, db_url=str(db_file))

    with TestClient(app=test_app) as client:
        yield client


def test_app_debug_is_false(client):
    """Verify that the app is NOT in debug mode during tests."""
    assert client.app.debug is False


def test_login_flow(client):
    get_login = client.get("/login")
    assert get_login.status_code == 200
    csrf_token = get_login.cookies.get("csrftoken")

    fail_secure = client.get("/secure")
    assert fail_secure.status_code == 401

    post_login = client.post(
        "/login",
        data={"username": "admin", "password": "secret"},
        headers={"x-csrf-token": csrf_token},
    )
    assert post_login.status_code == 303

    success_secure = client.get("/secure")
    assert success_secure.status_code == 200
