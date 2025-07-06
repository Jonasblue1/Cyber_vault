"""
Decentralized Reputation & Trust Scoring
Blockchain-based, privacy-preserving user/node reputation for CyberVault.
"""
import hashlib
import json
from blockchain.blockchain import Block
from backend.security import AESCipher
from backend.zkp import prove_loan_eligibility

REPUTATION_PREFIX = 'reputation:'

# Calculate reputation score

def calculate_reputation(user_id, tx_history, feedback=[]):
    # Compute a reputation score based on tx history and feedback
    score = sum(1 for tx in tx_history if tx.get('status') == 'completed')
    # Add feedback (ZKP stub)
    if feedback:
        proof = prove_loan_eligibility({'feedback': feedback})
        score += int(bool(proof))
    return hashlib.sha256(f'{user_id}:{score}'.encode()).hexdigest(), score

# Store reputation on blockchain (as encrypted data)
def store_reputation_on_chain(user_id, score, aes_key, blockchain_db):
    aes = AESCipher(aes_key)
    rep_data = json.dumps({'user_id': user_id, 'score': score})
    enc_data = aes.encrypt(rep_data).hex()
    block = Block(index=0, previous_hash='', timestamp='', data=enc_data)
    # Insert block into blockchain DB (assume blockchain_db is sqlite3 connection)
    c = blockchain_db.cursor()
    c.execute('INSERT INTO blockchain (block_hash, prev_hash, data, timestamp) VALUES (?, ?, ?, ?)',
              (block.hash, block.previous_hash, enc_data, ''))
    blockchain_db.commit()
    return block.hash

# Query reputation from blockchain (decrypt)
def query_reputation_from_chain(user_id, aes_key, blockchain_db):
    aes = AESCipher(aes_key)
    c = blockchain_db.cursor()
    c.execute('SELECT data FROM blockchain')
    for row in c.fetchall():
        try:
            data = bytes.fromhex(row[0])
            rep = json.loads(aes.decrypt(data))
            if rep.get('user_id') == user_id:
                return rep.get('score')
        except Exception:
            continue
    return None
