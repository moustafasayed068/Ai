"""Auth checks that need no Postgres, Supabase or Cohere account.

Run with:  pytest tests/test_security.py
"""
import os

for key in ("COHERE_API_KEY", "SECRET_KEY", "SUPABASE_KEY"):
    os.environ.setdefault(key, "test")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["DB_MODE"] = "local"
os.environ["ADMIN_EMAILS"] = "admin@example.com"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from App.db.session import get_db
from App.main import app
from App.models import User

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
User.__table__.create(engine)
Session = sessionmaker(bind=engine)


def _get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _get_db
client = TestClient(app)  # not used as a context manager, so startup create_all is skipped


def _token(email):
    client.post("/users/", json={"name": "t", "age": 20, "email": email, "password": "right-password"})
    r = client.post("/users/login", json={"email": email, "password": "right-password"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_login_requires_the_password():
    _token("user@example.com")
    r = client.post("/users/login", json={"email": "user@example.com", "password": "wrong"})
    assert r.status_code == 401


def test_no_token_without_password():
    assert client.post("/users/authenticate/00000000-0000-0000-0000-000000000000").status_code in (404, 405)


def test_admin_endpoints_are_admin_only():
    body = {"db_mode": "local"}
    assert client.post("/admin/db-mode", json=body).status_code in (401, 403)
    assert client.post("/admin/db-mode", json=body, headers=_token("user2@example.com")).status_code == 403
    assert client.post("/admin/db-mode", json=body, headers=_token("admin@example.com")).status_code == 200


def test_video_and_embedding_reads_need_login():
    assert client.get("/video/videos").status_code in (401, 403)
    assert client.get("/embedding/embed", params={"chat_id": "00000000-0000-0000-0000-000000000000"}).status_code in (401, 403)
