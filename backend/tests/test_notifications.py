from sqlalchemy.orm import Session

from app.models.enums import Gender, UserRole, VerificationStatus
from app.models.notification import Notification
from tests.conftest import auth_headers_for, create_admin_user, create_user


def test_user_verification_creates_user_notification(client, db_session: Session):
    admin = create_admin_user(db_session)
    rider = create_user(
        db_session,
        name="Aina Tan",
        email="notify-rider@sd.taylors.edu.my",
        role=UserRole.rider,
        gender=Gender.female,
        verification_status=VerificationStatus.pending,
        email_verified=True,
    )

    response = client.patch(
        f"/api/users/{rider.user_id}/verification",
        json={"verification_status": "approved"},
        headers=auth_headers_for(admin),
    )
    notifications_response = client.get("/api/notifications/me", headers=auth_headers_for(rider))

    assert response.status_code == 200
    assert notifications_response.status_code == 200
    notifications = notifications_response.json()
    assert notifications[0]["category"] == "verification"
    assert notifications[0]["entity_type"] == "user"
    assert notifications[0]["read_at"] is None


def test_notification_read_endpoints_are_user_scoped(client, db_session: Session):
    rider = create_user(
        db_session,
        name="Aina Tan",
        email="scoped-rider@sd.taylors.edu.my",
        role=UserRole.rider,
        gender=Gender.female,
    )
    other_user = create_user(
        db_session,
        name="Jason Wong",
        email="other-rider@sd.taylors.edu.my",
        role=UserRole.rider,
        gender=Gender.male,
        student_id="OTHER-R",
    )
    notification = Notification(
        user_id=rider.user_id,
        title="Trip status updated",
        body="Trip #1 is now ongoing.",
        category="trip",
        entity_type="trip",
        entity_id="1",
    )
    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)

    count_response = client.get("/api/notifications/me/unread-count", headers=auth_headers_for(rider))
    forbidden_response = client.patch(
        f"/api/notifications/{notification.notification_id}/read",
        headers=auth_headers_for(other_user),
    )
    read_response = client.patch(
        f"/api/notifications/{notification.notification_id}/read",
        headers=auth_headers_for(rider),
    )
    count_after_response = client.get("/api/notifications/me/unread-count", headers=auth_headers_for(rider))

    assert count_response.status_code == 200
    assert count_response.json()["unread_count"] == 1
    assert forbidden_response.status_code == 404
    assert read_response.status_code == 200
    assert read_response.json()["read_at"] is not None
    assert count_after_response.json()["unread_count"] == 0


def test_vehicle_submission_notifies_admins(client, db_session: Session):
    admin = create_admin_user(db_session)
    driver = create_user(
        db_session,
        name="Daniel Lim",
        email="notify-driver@sd.taylors.edu.my",
        role=UserRole.driver,
        gender=Gender.male,
    )

    response = client.post(
        "/api/vehicles",
        json={"plate_number": "NOT 1234", "vehicle_model": "Perodua Myvi", "seat_count": 4},
        headers=auth_headers_for(driver),
    )
    notifications_response = client.get("/api/notifications/me", headers=auth_headers_for(admin))

    assert response.status_code == 201
    assert notifications_response.status_code == 200
    assert notifications_response.json()[0]["category"] == "verification"
