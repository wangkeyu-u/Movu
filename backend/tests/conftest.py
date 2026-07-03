import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, get_password_hash
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.enums import Gender, UserRole, VerificationStatus
from app.models.user import User


engine = create_engine(
    "sqlite+pysqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session() -> Session:
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session: Session) -> TestClient:
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def create_admin_user(db: Session) -> User:
    admin = User(
        name="MovU Admin",
        email="admin@taylors.edu.my",
        student_id="ADM001",
        password_hash=get_password_hash("AdminPass123"),
        role=UserRole.admin,
        gender=Gender.prefer_not_to_say,
        verification_status=VerificationStatus.approved,
        email_verified=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def create_user(
    db: Session,
    *,
    name: str,
    email: str,
    role: UserRole,
    gender: Gender = Gender.prefer_not_to_say,
    student_id: str | None = None,
    password: str = "StrongPass123",
    verification_status: VerificationStatus = VerificationStatus.approved,
    email_verified: bool = True,
) -> User:
    user = User(
        name=name,
        email=email,
        student_id=student_id,
        password_hash=get_password_hash(password),
        role=role,
        gender=gender,
        verification_status=verification_status,
        email_verified=email_verified,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth_headers_for(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.email)}"}
