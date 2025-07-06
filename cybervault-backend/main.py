from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import hashlib
import os
import jwt
from typing import List, Optional

app = FastAPI(title="CyberVault Backend", description="Secure, offline-first micro-finance platform for conflict zones.")

# CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2/JWT setup (placeholder secret)
SECRET_KEY = os.environ.get("CYBERVAULT_SECRET_KEY", "supersecret")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# SQLite setup (offline-first)
DB_PATH = "cybervault.db"
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# User model (simplified)
class User(BaseModel):
    username: str
    password: str

# Transaction model
class Transaction(BaseModel):
    sender: str
    receiver: str
    amount: float
    timestamp: str
    signature: str
    status: str = "pending"  # pending, confirmed, failed

# Auth endpoints
@app.post("/auth/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Placeholder: Accept any user for demo
    user = {"username": form_data.username}
    token = jwt.encode(user, SECRET_KEY, algorithm="HS256")
    return {"access_token": token, "token_type": "bearer"}

# Transaction endpoints
@app.post("/transactions/queue")
def queue_transaction(tx: Transaction, token: str = Depends(oauth2_scheme)):
    # Store transaction locally (offline-first)
    db = get_db()
    db.execute(
        "INSERT INTO transactions (sender, receiver, amount, timestamp, signature, status) VALUES (?, ?, ?, ?, ?, ?)",
        (tx.sender, tx.receiver, tx.amount, tx.timestamp, tx.signature, tx.status)
    )
    db.commit()
    db.close()
    return {"message": "Transaction queued offline.", "tx": tx.dict()}

@app.get("/transactions/pending", response_model=List[Transaction])
def get_pending_transactions(token: str = Depends(oauth2_scheme)):
    db = get_db()
    rows = db.execute("SELECT * FROM transactions WHERE status = 'pending'").fetchall()
    db.close()
    return [Transaction(**dict(row)) for row in rows]

# Blockchain placeholder endpoint
@app.post("/blockchain/sync")
def sync_blockchain(token: str = Depends(oauth2_scheme)):
    # Placeholder for blockchain sync logic
    return {"message": "Blockchain sync endpoint (to be implemented)."}

# AI Fraud Detection placeholder endpoint
@app.post("/ai/fraud-detect")
def ai_fraud_detect(tx: Transaction, token: str = Depends(oauth2_scheme)):
    # Placeholder for AI fraud detection logic
    return {"fraud": False, "confidence": 0.01}

# DB init (run once)
def init_db():
    db = get_db()
    db.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        amount REAL,
        timestamp TEXT,
        signature TEXT,
        status TEXT
    )''')
    db.commit()
    db.close()

if __name__ == "__main__":
    init_db()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
