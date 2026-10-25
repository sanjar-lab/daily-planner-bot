"""Print a fresh ENCRYPTION_KEY for .env / Render."""
from cryptography.fernet import Fernet

print(Fernet.generate_key().decode())
