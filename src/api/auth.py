"""
Authentication service for M&A Diligence Swarm
"""
import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict
from pathlib import Path
import json
from loguru import logger


# Secret key for JWT (should be in environment variables in production)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours


class AuthService:
    """Authentication service"""
    
    def __init__(self, users_file: str = "data/users.json"):
        """Initialize auth service
        
        Args:
            users_file: Path to users database file
        """
        self.users_file = Path(users_file)
        self.users_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize with admin user if file doesn't exist
        if not self.users_file.exists():
            self._initialize_admin_user()
    
    def _initialize_admin_user(self):
        """Create initial admin user"""
        admin_email = "smaan2011@gmail.com"
        admin_password = "admin123"  # Change this immediately!
        
        users = {
            "users": [{
                "id": "admin-001",
                "email": admin_email,
                "password_hash": self._hash_password(admin_password),
                "role": "admin",
                "created_at": datetime.utcnow().isoformat()
            }]
        }
        
        with open(self.users_file, 'w') as f:
            json.dump(users, f, indent=2)
        
        logger.info(f"Initialized admin user: {admin_email}")
        logger.warning("IMPORTANT: Change the default admin password!")
    
    def _load_users(self) -> Dict:
        """Load users from file"""
        if not self.users_file.exists():
            return {"users": []}
        
        with open(self.users_file, 'r') as f:
            return json.load(f)
    
    def _save_users(self, users_data: Dict):
        """Save users to file"""
        with open(self.users_file, 'w') as f:
            json.dump(users_data, f, indent=2)
    
    def _hash_password(self, password: str) -> str:
        """Hash a password"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def create_user(self, email: str, password: str, role: str = "user") -> Dict:
        """Create a new user
        
        Args:
            email: User email
            password: User password
            role: User role (admin or user)
        
        Returns:
            User data (without password)
        
        Raises:
            ValueError: If user already exists
        """
        users_data = self._load_users()
        
        # Check if user already exists
        if any(u['email'] == email for u in users_data['users']):
            raise ValueError("User already exists")
        
        # Create new user
        user_id = f"user-{len(users_data['users']) + 1:03d}"
        new_user = {
            "id": user_id,
            "email": email,
            "password_hash": self._hash_password(password),
            "role": role,
            "created_at": datetime.utcnow().isoformat()
        }
        
        users_data['users'].append(new_user)
        self._save_users(users_data)
        
        logger.info(f"Created user: {email} (role: {role})")
        
        # Return user without password
        return {
            "id": new_user["id"],
            "email": new_user["email"],
            "role": new_user["role"],
            "created_at": new_user["created_at"]
        }
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        """Authenticate a user
        
        Args:
            email: User email
            password: User password
        
        Returns:
            User data if authenticated, None otherwise
        """
        users_data = self._load_users()
        
        for user in users_data['users']:
            if user['email'] == email:
                if self._verify_password(password, user['password_hash']):
                    return {
                        "id": user["id"],
                        "email": user["email"],
                        "role": user["role"],
                        "created_at": user["created_at"]
                    }
                return None
        
        return None
    
    def create_access_token(self, user_data: Dict) -> str:
        """Create JWT access token
        
        Args:
            user_data: User data to encode
        
        Returns:
            JWT token string
        """
        expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode = {
            "sub": user_data["email"],
            "user_id": user_data["id"],
            "role": user_data["role"],
            "exp": expires
        }
        
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token
        
        Args:
            token: JWT token string
        
        Returns:
            Decoded token data if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email
        
        Args:
            email: User email
        
        Returns:
            User data (without password) if found, None otherwise
        """
        users_data = self._load_users()
        
        for user in users_data['users']:
            if user['email'] == email:
                return {
                    "id": user["id"],
                    "email": user["email"],
                    "role": user["role"],
                    "created_at": user["created_at"]
                }
        
        return None
    
    def is_admin(self, user_email: str) -> bool:
        """Check if user is admin
        
        Args:
            user_email: User email
        
        Returns:
            True if user is admin, False otherwise
        """
        user = self.get_user_by_email(user_email)
        return user is not None and user['role'] == 'admin'
    
    def list_all_users(self) -> list:
        """List all users
        
        Returns:
            List of all users (without passwords)
        """
        users_data = self._load_users()
        return [
            {
                "id": user["id"],
                "email": user["email"],
                "role": user["role"],
                "created_at": user["created_at"]
            }
            for user in users_data['users']
        ]
    
    def delete_user(self, user_id: str) -> bool:
        """Delete a user by ID
        
        Args:
            user_id: User ID to delete
        
        Returns:
            True if user was deleted, False if not found
        """
        users_data = self._load_users()
        
        # Find and remove user
        initial_count = len(users_data['users'])
        users_data['users'] = [u for u in users_data['users'] if u['id'] != user_id]
        
        if len(users_data['users']) < initial_count:
            self._save_users(users_data)
            logger.info(f"Deleted user: {user_id}")
            return True
        
        return False
