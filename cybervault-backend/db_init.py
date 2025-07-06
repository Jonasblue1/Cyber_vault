import sqlite3

def init_db():
    conn = sqlite3.connect('cybervault.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        email TEXT,
        mfa_enabled BOOLEAN DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        amount REAL,
        timestamp TEXT,
        signature TEXT,
        status TEXT,
        blockchain_hash TEXT,
        fraud_flag BOOLEAN DEFAULT 0,
        fraud_score REAL DEFAULT 0.0
    )''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("CyberVault DB initialized.")
