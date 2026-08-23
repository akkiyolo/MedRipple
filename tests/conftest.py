import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.core.security import hash_password, create_access_token
from main import app

# In-memory SQLite for rapid isolated unit testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def test_patient_user(db_session):
    user = User(
        email="patient@test.com",
        password_hash=hash_password("password123"),
        role=UserRole.PATIENT,
        is_active=True
    )
    db_session.add(user)
    db_session.flush()

    patient = Patient(
        user_id=user.id,
        name="Test Patient",
        phone="+15550199"
    )
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_doctor_user(db_session):
    user = User(
        email="doctor@test.com",
        password_hash=hash_password("password123"),
        role=UserRole.DOCTOR,
        is_active=True
    )
    db_session.add(user)
    db_session.flush()

    doctor = Doctor(
        user_id=user.id,
        name="Dr. Sarah Test",
        specialization="Pulmonology",
        license_number="MD998877",
        slot_duration=30
    )
    db_session.add(doctor)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def patient_token(test_patient_user):
    return create_access_token({"sub": str(test_patient_user.id), "email": test_patient_user.email, "role": "PATIENT"})

@pytest.fixture
def doctor_token(test_doctor_user):
    return create_access_token({"sub": str(test_doctor_user.id), "email": test_doctor_user.email, "role": "DOCTOR"})
