import sys
import os
import getpass # Allows typing password without showing it on screen

# 1. Setup Python Path to find the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def create_new_user():
    print("👤 --- AEGIS USER CREATION WIZARD ---")
    
    # 2. Get Input
    username = input("Enter new username: ").strip()
    
    if not username:
        print("❌ Username cannot be empty.")
        return

    # 3. Check Database
    db = SessionLocal()
    existing_user = db.query(User).filter(User.username == username).first()
    
    if existing_user:
        print(f"❌ Error: User '{username}' already exists.")
        db.close()
        return

    # 4. Get Password securely
    password = getpass.getpass(f"Enter password for {username}: ")
    confirm_pass = getpass.getpass("Confirm password: ")

    if password != confirm_pass:
        print("❌ Passwords do not match.")
        db.close()
        return

    # 5. Create User
    try:
        new_user = User(
            username=username,
            hashed_password=get_password_hash(password),
            is_superuser=False # Default to normal user
        )
        db.add(new_user)
        db.commit()
        print(f"✅ SUCCESS: User '{username}' has been added to the secure database.")
    except Exception as e:
        print(f"❌ Database Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_new_user()