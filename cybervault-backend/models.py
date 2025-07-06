from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    mfa_enabled: bool = False

class Transaction(BaseModel):
    sender: str
    receiver: str
    amount: float
    timestamp: str
    signature: str
    status: str = "pending"  # pending, confirmed, failed
    blockchain_hash: Optional[str] = None
    fraud_flag: Optional[bool] = False
    fraud_score: Optional[float] = 0.0
