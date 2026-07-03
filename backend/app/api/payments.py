from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_current_user, require_approved_user, require_roles
from app.db.session import get_db
from app.models.enums import MatchStatus, PaymentMethod, PaymentStatus, UserRole
from app.models.match import RideMatch
from app.models.payment import Payment
from app.models.user import User
from app.schemas.payment import PaymentRead, PaymentSimulationRequest, PaymentSimulationResponse
from app.services.payments import calculate_fare


router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/matches/{match_id}/simulate", response_model=PaymentSimulationResponse)
def simulate_ewallet_payment(
    match_id: int,
    payload: PaymentSimulationRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_user),
) -> PaymentSimulationResponse:
    if settings.environment == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Simulated payments are disabled in production",
        )

    match = db.get(RideMatch, match_id)
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    if match.status != MatchStatus.confirmed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only confirmed matches can be paid")
    if current_user.user_id != match.rider_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")

    existing_paid_payment = (
        db.query(Payment)
        .filter(
            Payment.match_id == match.match_id,
            Payment.payer_id == match.rider_id,
            Payment.payment_status == PaymentStatus.paid,
        )
        .first()
    )
    if existing_paid_payment is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Match has already been paid")

    distance_km = match.ride_request.distance_km
    if payload and payload.distance_km is not None:
        distance_km = payload.distance_km
        match.ride_request.distance_km = distance_km
    if distance_km is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Distance is required")

    fare = calculate_fare(distance_km, match.ride_request.passenger_count)
    payment = Payment(
        match_id=match.match_id,
        payer_id=match.rider_id,
        amount=fare.fare_per_passenger,
        payment_status=PaymentStatus.paid,
        payment_method=PaymentMethod.simulated_ewallet,
    )
    db.add_all([match.ride_request, payment])
    db.commit()
    db.refresh(payment)
    return PaymentSimulationResponse(payment=payment, **fare.__dict__)


@router.get("/me", response_model=list[PaymentRead])
def list_my_payments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Payment]:
    return (
        db.query(Payment)
        .filter(Payment.payer_id == current_user.user_id)
        .order_by(Payment.created_at.desc())
        .all()
    )


@router.get("", response_model=list[PaymentRead])
def list_payments(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
    payment_status: PaymentStatus | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[Payment]:
    query = db.query(Payment)
    if payment_status is not None:
        query = query.filter(Payment.payment_status == payment_status)
    return query.order_by(Payment.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{payment_id}", response_model=PaymentRead)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Payment:
    payment = db.get(Payment, payment_id)
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    if current_user.role != UserRole.admin and payment.payer_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    return payment
