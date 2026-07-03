from sqlalchemy.orm import Session

from app.models.user import User
from app.models.audit_log import AuditLog
from app.services.email_verification import issue_email_verification
from tests.conftest import auth_headers_for, create_admin_user


def rider_payload(email: str = "rider1@sd.taylors.edu.my") -> dict[str, str]:
    return {
        "name": "Aina Tan",
        "email": email,
        "student_id": "SID1001",
        "password": "StrongPass123",
        "role": "rider",
        "gender": "female",
    }


def test_register_rejects_non_taylors_email(client):
    payload = rider_payload(email="aina@gmail.com")

    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 422


def test_register_rejects_public_admin_signup(client):
    payload = rider_payload(email="notadmin@taylors.edu.my")
    payload["role"] = "admin"

    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 422


def test_register_requires_email_verification_before_login(client):
    register_response = client.post("/api/auth/register", json=rider_payload())

    assert register_response.status_code == 201
    user = register_response.json()
    assert user["email"] == "rider1@sd.taylors.edu.my"
    assert user["role"] == "rider"
    assert user["verification_status"] == "pending"
    assert "password_hash" not in user

    login_response = client.post(
        "/api/auth/login",
        json={"email": "rider1@sd.taylors.edu.my", "password": "StrongPass123"},
    )

    assert login_response.status_code == 403


def test_verify_email_then_login_returns_token(client, db_session: Session):
    client.post("/api/auth/register", json=rider_payload())
    user = db_session.query(User).filter(User.email == "rider1@sd.taylors.edu.my").one()
    token = issue_email_verification(db_session, user)

    verify_response = client.post("/api/auth/verify-email", json={"token": token})
    login_response = client.post(
        "/api/auth/login",
        json={"email": "rider1@sd.taylors.edu.my", "password": "StrongPass123"},
    )

    assert verify_response.status_code == 200
    assert verify_response.json()["email_verified"] is True
    assert login_response.status_code == 200
    body = login_response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "rider1@sd.taylors.edu.my"


def test_me_returns_current_user(client, db_session: Session):
    client.post("/api/auth/register", json=rider_payload())
    user = db_session.query(User).filter(User.email == "rider1@sd.taylors.edu.my").one()
    token = issue_email_verification(db_session, user)
    client.post("/api/auth/verify-email", json={"token": token})

    login_response = client.post(
        "/api/auth/login",
        json={"email": "rider1@sd.taylors.edu.my", "password": "StrongPass123"},
    )
    token = login_response.json()["access_token"]

    response = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == "rider1@sd.taylors.edu.my"


def test_admin_can_list_and_verify_users(client, db_session: Session):
    admin = create_admin_user(db_session)
    client.post("/api/auth/register", json=rider_payload())
    rider = db_session.query(User).filter(User.email == "rider1@sd.taylors.edu.my").one()

    list_response = client.get("/api/users", headers=auth_headers_for(admin))
    verify_response = client.patch(
        f"/api/users/{rider.user_id}/verification",
        json={"verification_status": "approved"},
        headers=auth_headers_for(admin),
    )

    assert list_response.status_code == 200
    assert len(list_response.json()) == 2
    assert verify_response.status_code == 200
    assert verify_response.json()["verification_status"] == "approved"


def test_admin_can_ban_user_and_login_is_blocked(client, db_session: Session):
    admin = create_admin_user(db_session)
    client.post("/api/auth/register", json=rider_payload())
    rider = db_session.query(User).filter(User.email == "rider1@sd.taylors.edu.my").one()
    token = issue_email_verification(db_session, rider)
    client.post("/api/auth/verify-email", json={"token": token})

    ban_response = client.patch(
        f"/api/users/{rider.user_id}/ban",
        headers=auth_headers_for(admin),
    )
    login_response = client.post(
        "/api/auth/login",
        json={"email": "rider1@sd.taylors.edu.my", "password": "StrongPass123"},
    )

    assert ban_response.status_code == 200
    assert ban_response.json()["is_banned"] is True
    assert login_response.status_code == 403
    audit_log = db_session.query(AuditLog).filter(AuditLog.action == "user.banned").one()
    assert audit_log.entity_id == str(rider.user_id)
