from datetime import UTC, datetime, timedelta

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.enums import (
    Gender,
    GenderPreference,
    MatchStatus,
    PaymentMethod,
    PaymentStatus,
    ReportType,
    RideRequestStatus,
    SOSStatus,
    TripStatus,
    UserRole,
    VerificationStatus,
)
from app.models.location_log import LocationLog
from app.models.match import RideMatch
from app.models.payment import Payment
from app.models.rating_report import RatingReport
from app.models.ride_request import RideRequest
from app.models.sos_event import SOSEvent
from app.models.trip import Trip
from app.models.user import User
from app.models.vehicle import Vehicle


DEFAULT_PASSWORD = "Password123"


def reset_database() -> None:
    if settings.environment == "production":
        raise RuntimeError("Refusing to reset a production database")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def seed() -> None:
    if settings.environment == "production":
        raise RuntimeError("Seed data is not allowed in production")
    reset_database()
    db = SessionLocal()
    try:
        now = datetime.now(UTC)

        admin = User(
            name="MovU Admin",
            email="admin@taylors.edu.my",
            student_id="ADM001",
            password_hash=get_password_hash(DEFAULT_PASSWORD),
            role=UserRole.admin,
            gender=Gender.prefer_not_to_say,
            verification_status=VerificationStatus.approved,
            email_verified=True,
        )
        riders = [
            User(
                name="Aina Tan",
                email="aina@sd.taylors.edu.my",
                student_id="R001",
                password_hash=get_password_hash(DEFAULT_PASSWORD),
                role=UserRole.rider,
                gender=Gender.female,
                verification_status=VerificationStatus.approved,
                email_verified=True,
            ),
            User(
                name="Jason Lee",
                email="jason@sd.taylors.edu.my",
                student_id="R002",
                password_hash=get_password_hash(DEFAULT_PASSWORD),
                role=UserRole.rider,
                gender=Gender.male,
                verification_status=VerificationStatus.approved,
                email_verified=True,
            ),
            User(
                name="Siti Nur",
                email="siti@sd.taylors.edu.my",
                student_id="R003",
                password_hash=get_password_hash(DEFAULT_PASSWORD),
                role=UserRole.rider,
                gender=Gender.female,
                verification_status=VerificationStatus.pending,
                email_verified=True,
            ),
        ]
        drivers = [
            User(
                name="Daniel Lim",
                email="daniel@sd.taylors.edu.my",
                student_id="D001",
                password_hash=get_password_hash(DEFAULT_PASSWORD),
                role=UserRole.driver,
                gender=Gender.male,
                rating=4.8,
                verification_status=VerificationStatus.approved,
                email_verified=True,
            ),
            User(
                name="Mei Wong",
                email="mei@sd.taylors.edu.my",
                student_id="D002",
                password_hash=get_password_hash(DEFAULT_PASSWORD),
                role=UserRole.driver,
                gender=Gender.female,
                rating=4.6,
                verification_status=VerificationStatus.approved,
                email_verified=True,
            ),
            User(
                name="Hakim Azman",
                email="hakim@taylors.edu.my",
                student_id="D003",
                password_hash=get_password_hash(DEFAULT_PASSWORD),
                role=UserRole.driver,
                gender=Gender.male,
                rating=4.4,
                verification_status=VerificationStatus.approved,
                email_verified=True,
            ),
        ]
        db.add_all([admin, *riders, *drivers])
        db.commit()
        for user in [admin, *riders, *drivers]:
            db.refresh(user)

        vehicles = [
            Vehicle(
                driver_id=drivers[0].user_id,
                plate_number="VBN1234",
                vehicle_model="Perodua Myvi",
                seat_count=4,
                verification_status=VerificationStatus.approved,
            ),
            Vehicle(
                driver_id=drivers[1].user_id,
                plate_number="WXY8080",
                vehicle_model="Honda City",
                seat_count=4,
                verification_status=VerificationStatus.approved,
            ),
            Vehicle(
                driver_id=drivers[2].user_id,
                plate_number="BMA2026",
                vehicle_model="Toyota Vios",
                seat_count=4,
                verification_status=VerificationStatus.approved,
            ),
        ]
        db.add_all(vehicles)
        db.commit()

        ride_requests = [
            RideRequest(
                rider_id=riders[0].user_id,
                origin="Taylor's Lakeside Campus",
                destination="Sunway Pyramid",
                origin_latitude=3.0646,
                origin_longitude=101.6159,
                destination_latitude=3.0738,
                destination_longitude=101.6070,
                preferred_time=now + timedelta(minutes=35),
                passenger_count=2,
                gender_preference=GenderPreference.none,
                distance_km=5.2,
                status=RideRequestStatus.pending,
            ),
            RideRequest(
                rider_id=riders[1].user_id,
                origin="Taylor's Lakeside Campus",
                destination="KL Sentral",
                origin_latitude=3.0646,
                origin_longitude=101.6159,
                destination_latitude=3.1340,
                destination_longitude=101.6868,
                preferred_time=now + timedelta(minutes=50),
                passenger_count=1,
                gender_preference=GenderPreference.none,
                distance_km=18.0,
                status=RideRequestStatus.matched,
            ),
            RideRequest(
                rider_id=riders[2].user_id,
                origin="DK Senza",
                destination="Taylor's Lakeside Campus",
                origin_latitude=3.0658,
                origin_longitude=101.6123,
                destination_latitude=3.0646,
                destination_longitude=101.6159,
                preferred_time=now + timedelta(minutes=70),
                passenger_count=1,
                gender_preference=GenderPreference.same_gender,
                distance_km=2.1,
                status=RideRequestStatus.pending,
            ),
            RideRequest(
                rider_id=riders[0].user_id,
                origin="Taylor's Lakeside Campus",
                destination="Subang Jaya LRT",
                origin_latitude=3.0646,
                origin_longitude=101.6159,
                destination_latitude=3.0845,
                destination_longitude=101.5881,
                preferred_time=now - timedelta(hours=3, minutes=5),
                passenger_count=1,
                gender_preference=GenderPreference.none,
                distance_km=6.1,
                status=RideRequestStatus.completed,
            ),
        ]
        trips = [
            Trip(
                driver_id=drivers[0].user_id,
                origin="Taylor's Lakeside Campus",
                destination="Sunway Pyramid",
                origin_latitude=3.0646,
                origin_longitude=101.6159,
                destination_latitude=3.0738,
                destination_longitude=101.6070,
                departure_time=now + timedelta(minutes=40),
                available_seats=4,
                total_seats=4,
                status=TripStatus.posted,
            ),
            Trip(
                driver_id=drivers[1].user_id,
                origin="Taylor's Lakeside Campus",
                destination="KL Sentral",
                origin_latitude=3.0646,
                origin_longitude=101.6159,
                destination_latitude=3.1340,
                destination_longitude=101.6868,
                departure_time=now + timedelta(minutes=55),
                available_seats=3,
                total_seats=4,
                status=TripStatus.ongoing,
            ),
            Trip(
                driver_id=drivers[2].user_id,
                origin="Taylor's Lakeside Campus",
                destination="Subang Jaya LRT",
                origin_latitude=3.0646,
                origin_longitude=101.6159,
                destination_latitude=3.0845,
                destination_longitude=101.5881,
                departure_time=now - timedelta(hours=3),
                available_seats=2,
                total_seats=4,
                status=TripStatus.completed,
            ),
            Trip(
                driver_id=drivers[1].user_id,
                origin="DK Senza",
                destination="Taylor's Lakeside Campus",
                origin_latitude=3.0658,
                origin_longitude=101.6123,
                destination_latitude=3.0646,
                destination_longitude=101.6159,
                departure_time=now + timedelta(minutes=75),
                available_seats=4,
                total_seats=4,
                status=TripStatus.posted,
            ),
        ]
        db.add_all([*ride_requests, *trips])
        db.commit()
        for item in [*ride_requests, *trips]:
            db.refresh(item)

        matches = [
            RideMatch(
                trip_id=trips[0].trip_id,
                request_id=ride_requests[0].request_id,
                rider_id=riders[0].user_id,
                match_score=94.2,
                status=MatchStatus.recommended,
            ),
            RideMatch(
                trip_id=trips[1].trip_id,
                request_id=ride_requests[1].request_id,
                rider_id=riders[1].user_id,
                match_score=91.5,
                status=MatchStatus.confirmed,
            ),
            RideMatch(
                trip_id=trips[3].trip_id,
                request_id=ride_requests[2].request_id,
                rider_id=riders[2].user_id,
                match_score=88.0,
                status=MatchStatus.recommended,
            ),
            RideMatch(
                trip_id=trips[2].trip_id,
                request_id=ride_requests[3].request_id,
                rider_id=riders[0].user_id,
                match_score=90.8,
                status=MatchStatus.completed,
            ),
        ]
        db.add_all(matches)
        db.commit()
        for match in matches:
            db.refresh(match)

        db.add_all(
            [
                Payment(
                    match_id=matches[1].match_id,
                    payer_id=riders[1].user_id,
                    amount=24.6,
                    payment_status=PaymentStatus.paid,
                    payment_method=PaymentMethod.simulated_ewallet,
                ),
                Payment(
                    match_id=matches[3].match_id,
                    payer_id=riders[0].user_id,
                    amount=10.32,
                    payment_status=PaymentStatus.refunded,
                    payment_method=PaymentMethod.simulated_ewallet,
                ),
            ]
        )
        db.add_all(
            [
                LocationLog(
                    trip_id=trips[1].trip_id,
                    user_id=drivers[1].user_id,
                    latitude=3.0633,
                    longitude=101.6169,
                ),
                LocationLog(
                    trip_id=trips[1].trip_id,
                    user_id=drivers[1].user_id,
                    latitude=3.0821,
                    longitude=101.6339,
                ),
                LocationLog(
                    trip_id=trips[2].trip_id,
                    user_id=drivers[2].user_id,
                    latitude=3.0845,
                    longitude=101.5881,
                ),
            ]
        )
        db.add_all(
            [
                SOSEvent(
                    user_id=riders[1].user_id,
                    trip_id=trips[1].trip_id,
                    latitude=3.0633,
                    longitude=101.6169,
                    status=SOSStatus.new,
                ),
                SOSEvent(
                    user_id=riders[0].user_id,
                    trip_id=trips[2].trip_id,
                    latitude=3.0845,
                    longitude=101.5881,
                    status=SOSStatus.resolved,
                    resolved_time=now - timedelta(hours=1),
                ),
                SOSEvent(
                    user_id=drivers[2].user_id,
                    trip_id=trips[2].trip_id,
                    latitude=3.0820,
                    longitude=101.5900,
                    status=SOSStatus.false_alarm,
                    resolved_time=now - timedelta(minutes=45),
                ),
            ]
        )
        db.add_all(
            [
                RatingReport(
                    from_user_id=riders[0].user_id,
                    to_user_id=drivers[2].user_id,
                    trip_id=trips[2].trip_id,
                    score=5,
                    comment="Smooth ride and clear communication",
                ),
                RatingReport(
                    from_user_id=drivers[2].user_id,
                    to_user_id=riders[0].user_id,
                    trip_id=trips[2].trip_id,
                    score=5,
                    comment="Ready at pickup and polite throughout the trip",
                ),
                RatingReport(
                    from_user_id=riders[1].user_id,
                    to_user_id=drivers[0].user_id,
                    trip_id=trips[0].trip_id,
                    report_type=ReportType.late,
                    comment="Pickup was delayed during peak time",
                ),
                RatingReport(
                    from_user_id=riders[0].user_id,
                    to_user_id=drivers[2].user_id,
                    trip_id=trips[2].trip_id,
                    report_type=ReportType.other,
                    comment="Asked admin to review the refunded payment record",
                ),
            ]
        )
        db.commit()
        print("Seed data created.")
        print(f"Admin: admin@taylors.edu.my / {DEFAULT_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
