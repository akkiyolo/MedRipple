from app.core.database import SessionLocal, Base, engine
from sqlalchemy import text

db = SessionLocal()
result = db.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users');")).scalar()
print("Users table exists:", result)

if not result:
    print("Forcing schema creation...")
    # Import all models here so SQLAlchemy knows about them before create_all
    import app.models.user
    import app.models.patient
    import app.models.doctor
    import app.models.doctor_schedule
    import app.models.appointment
    import app.models.notification
    
    # Try creating tables, ignore ENUM existing errors
    try:
        Base.metadata.create_all(bind=engine)
        print("Created all tables successfully.")
    except Exception as e:
        print(f"Error during create_all: {e}")
        
    result2 = db.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users');")).scalar()
    print("Users table exists after force:", result2)
