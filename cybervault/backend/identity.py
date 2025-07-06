"""
Decentralized Identity - Hashed user IDs and local authentication
"""
import hashlib

def create_user_id(username):
    return hashlib.sha256(username.encode()).hexdigest()

def authenticate_user(username, pin_hash, input_pin):
    return create_user_id(username) and (hashlib.sha256(input_pin.encode()).hexdigest() == pin_hash)
