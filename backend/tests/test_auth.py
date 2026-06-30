import unittest
import time
from app.api.routes.auth import hash_password, verify_password, create_access_token
import jwt

class TestAuthentication(unittest.TestCase):
    def test_password_hashing(self) -> None:
        password = "secret_password_123"
        hashed = hash_password(password)
        
        # Verify format (salt:hash separator)
        self.assertIn(":", hashed)
        
        # Verify valid validation
        self.assertTrue(verify_password(password, hashed))
        
        # Verify invalid validation
        self.assertFalse(verify_password("wrong_password", hashed))

    def test_token_creation(self) -> None:
        username = "test_user"
        role = "admin"
        
        token = create_access_token(username, role)
        self.assertIsNotNone(token)
        
        # Verify JWT can be decoded with secret key
        from app.api.routes.auth import JWT_SECRET, JWT_ALGORITHM
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        self.assertEqual(payload.get("sub"), username)
        self.assertEqual(payload.get("role"), role)
        self.assertGreater(payload.get("exp"), time.time())
