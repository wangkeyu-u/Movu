from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_approved_user, require_roles
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.rating_report import RatingReport
from app.models.user import User
from app.schemas.report import RatingCreate, RatingReportRead, ReportCreate
from app.services.ratings import assert_trip_completed_and_participants, recalculate_user_rating


router = APIRouter(prefix="/reports", tags=["ratings and reports"])


@router.post("/ratings", response_model=RatingReportRead, status_code=status.HTTP_201_CREATED)
def create_rating(
    payload: RatingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_user),
) -> RatingReport:
    assert_trip_completed_and_participants(
        db,
        from_user=current_user,
        to_user_id=payload.to_user_id,
        trip_id=payload.trip_id,
    )
    rating = RatingReport(
        from_user_id=current_user.user_id,
        to_user_id=payload.to_user_id,
        trip_id=payload.trip_id,
        score=payload.score,
        comment=payload.comment,
    )
    db.add(rating)
    db.commit()
    db.refresh(rating)
    recalculate_user_rating(db, payload.to_user_id)
    return rating


@router.post("", response_model=RatingReportRead, status_code=status.HTTP_201_CREATED)
def create_report(
    payload: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_user),
) -> RatingReport:
    assert_trip_completed_and_participants(
        db,
        from_user=current_user,
        to_user_id=payload.to_user_id,
        trip_id=payload.trip_id,
    )
    report = RatingReport(
        from_user_id=current_user.user_id,
        to_user_id=payload.to_user_id,
        trip_id=payload.trip_id,
        score=payload.score,
        report_type=payload.report_type,
        comment=payload.comment,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    if payload.score is not None:
        recalculate_user_rating(db, payload.to_user_id)
    return report


@router.get("/me", response_model=list[RatingReportRead])
def list_my_rating_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    direction: str = Query(default="received", pattern="^(received|given)$"),
) -> list[RatingReport]:
    query = db.query(RatingReport)
    if direction == "given":
        query = query.filter(RatingReport.from_user_id == current_user.user_id)
    else:
        query = query.filter(RatingReport.to_user_id == current_user.user_id)
    return query.order_by(RatingReport.created_at.desc()).all()


@router.get("", response_model=list[RatingReportRead])
def list_rating_reports(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[RatingReport]:
    return db.query(RatingReport).order_by(RatingReport.created_at.desc()).offset(skip).limit(limit).all()
