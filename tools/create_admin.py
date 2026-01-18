import sys
import os

# 1. Setup Python Path so it can find 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal, engine, Base
from app.models.user import User
from app.models.scan import ScanLog # Import this so the DB knows about Scans too
from app.core.security import get_password_hash

def create_admin():
    # --- CRITICAL FIX: Create Tables if they don't exist ---
    print("🛠️  Checking Database Tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database Tables Verified.")
    # -------------------------------------------------------

    db = SessionLocal()
    
    try:
        # Check if admin exists
        user = db.query(User).filter(User.username == "admin").first()
        if user:
            print("⚠️  Admin user already exists.")
            return

        # Create Admin
        print("👤 Creating Admin User...")
        admin_user = User(
            username="admin",
            hashed_password=get_password_hash("admin123"), # You can change this
            is_superuser=True
        )
        db.add(admin_user)
        db.commit()
        print("✅ SUCCESS: User 'admin' created with password 'admin123'")
        
    except Exception as e:
        print(f"❌ Error creating admin: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()